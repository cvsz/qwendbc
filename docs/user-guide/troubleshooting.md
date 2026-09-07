# Troubleshooting Guide

Common issues and solutions for QwenDBC.

## Quick Diagnostic Steps

Before diving into specific issues:

1. **Check service status**: `docker-compose ps`
2. **View logs**: `docker-compose logs --tail=50`
3. **Verify ports**: `netstat -tlnp | grep -E '8000|3000'`
4. **Test health endpoint**: `curl http://localhost:8000/api/v1/health`

---

## Model Loading Issues

### Issue: Model Won't Load

**Symptoms:**
- "Load Model" button shows error
- Status remains "Not Loaded"
- Timeout after clicking load

**Possible Causes & Solutions:**

#### 1. Insufficient RAM

**Diagnosis:**
```bash
free -h
docker stats
```

**Solution:**
- Close memory-intensive applications
- Use smaller model variant (e.g., q4_k_m instead of q8_0)
- Add swap space:
  ```bash
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  ```

#### 2. Download Failure

**Diagnosis:**
```bash
docker-compose logs backend | grep -i "download\|error"
```

**Solution:**
- Check internet connectivity: `ping huggingface.co`
- Verify HuggingFace accessibility: `curl https://huggingface.co`
- Manually download model:
  ```bash
  cd models
  wget https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
  ```
- Check proxy settings if behind corporate firewall

#### 3. Disk Space Full

**Diagnosis:**
```bash
df -h
```

**Solution:**
```bash
# Clean up Docker
docker system prune -a

# Remove old models
rm -rf models/*

# Clear ChromaDB if not needed
rm -rf chroma_db/*
```

#### 4. CPU Thread Configuration

**Symptoms:** Model loads but system becomes unresponsive

**Solution:**
Reduce thread count in `.env`:
```env
N_THREADS=2
MAX_CONTEXT_LENGTH=2048
```

---

## Performance Issues

### Issue: Slow Response Times

**Symptoms:**
- Responses take >30 seconds
- System lag during inference
- High CPU usage sustained

**Diagnosis:**
```bash
# Monitor CPU
top -p $(pgrep -f "uvicorn")

# Check memory pressure
vmstat 1 5

# View request timing
docker-compose logs backend | grep "response_time"
```

**Solutions:**

#### 1. Optimize Model Settings

```env
# Reduce context length
MAX_CONTEXT_LENGTH=2048

# Limit response length
MAX_TOKENS=512

# Reduce batch size
N_BATCH=256
```

#### 2. Resource Allocation

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
```

#### 3. Use Smaller Model

Switch to more aggressive quantization:
```env
MODEL_FILE=qwen2.5-1.5b-instruct-q2_k.gguf
```

#### 4. Clear Conversation History

Long conversations consume more resources. Click "Clear Chat" periodically.

---

### Issue: Out of Memory (OOM)

**Symptoms:**
- Container crashes unexpectedly
- "Killed" message in logs
- System becomes unresponsive

**Diagnosis:**
```bash
dmesg | grep -i "killed process"
docker inspect qwen-backend | grep -A 10 "OOMKilled"
```

**Solutions:**

#### 1. Increase Memory Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G
```

#### 2. Use Smaller Model

```env
MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct-GGUF
```

#### 3. Enable Swap

```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
```

#### 4. Unload When Not in Use

Use API to unload model when idle:
```bash
curl -X POST http://localhost:8000/api/v1/model/unload
```

---

## Connection Issues

### Issue: Frontend Can't Connect to Backend

**Symptoms:**
- "Connection failed" error
- Model status shows "Error"
- Network tab shows failed requests

**Diagnosis:**
```bash
# Check if backend is running
docker-compose ps backend

# Test backend directly
curl http://localhost:8000/api/v1/health

# Check CORS errors in browser console
```

**Solutions:**

#### 1. Restart Services

```bash
docker-compose restart backend frontend
```

#### 2. Verify Port Availability

```bash
# Check if ports are in use
netstat -tlnp | grep -E '8000|3000'

# Kill conflicting processes if needed
sudo lsof -ti:8000 | xargs kill -9
```

#### 3. Check CORS Configuration

Ensure `.env` has correct origins:
```env
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

#### 4. Rebuild Containers

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

### Issue: API Returns 500 Errors

**Symptoms:**
- HTTP 500 Internal Server Error
- Error messages in response
- Backend logs show exceptions

**Diagnosis:**
```bash
docker-compose logs backend | grep -A 5 "ERROR"
```

**Common Causes:**

#### 1. Model Not Loaded

**Solution:**
```bash
curl -X POST http://localhost:8000/api/v1/model/load
```

#### 2. Invalid Request Format

**Solution:** Verify request matches schema:
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

#### 3. Backend Crash

**Solution:**
```bash
docker-compose restart backend
docker-compose logs --tail=100 backend
```

---

## Frontend Issues

### Issue: Blank Page or Loading Forever

**Symptoms:**
- White screen
- perpetual loading spinner
- No content rendered

**Diagnosis:**
Open browser DevTools (F12) and check Console tab

**Solutions:**

#### 1. Build Errors

```bash
cd frontend
npm run build
```

#### 2. Environment Variable Missing

Ensure `.env` exists in frontend directory:
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

#### 3. Clear Browser Cache

- Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
- Clear site data in browser settings
- Try incognito/private mode

#### 4. Rebuild Frontend

```bash
docker-compose down frontend
docker-compose build frontend
docker-compose up -d frontend
```

---

### Issue: Messages Not Sending

**Symptoms:**
- Send button disabled
- Input field grayed out
- Error on send attempt

**Solutions:**

#### 1. Check Model Status

Model must be loaded before chatting. Click "Load Model".

#### 2. Clear Input

Empty input disables send button. Type a message.

#### 3. Check Network

Verify backend is responding:
```bash
curl http://localhost:8000/api/v1/health
```

---

## Logging & Debugging

### Enable Debug Mode

Set in `.env`:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last N lines
docker-compose logs --tail=100

# With timestamps
docker-compose logs -ft
```

### Export Logs

```bash
docker-compose logs > full_logs.txt
```

---

## Database Issues (ChromaDB)

### Issue: Vector Store Corruption

**Symptoms:**
- Embedding generation fails
- Collection errors
- Data inconsistency

**Solutions:**

#### 1. Reset ChromaDB

```bash
docker-compose down
rm -rf chroma_db/*
docker-compose up -d
```

#### 2. Check Disk Permissions

```bash
sudo chown -R 1000:1000 chroma_db
```

#### 3. Verify Volume Mount

Ensure volume is correctly mounted in `docker-compose.yml`:
```yaml
volumes:
  - ./chroma_db:/app/chroma_db
```

---

## Recovery Procedures

### Complete Reset

When all else fails:

```bash
# Stop everything
docker-compose down -v

# Remove all containers
docker rm -f $(docker ps -aq)

# Remove images
docker rmi $(docker images -q qwen*)

# Clean directories
rm -rf models/* chroma_db/*

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

### Backup Before Reset

```bash
# Backup important data
cp -r chroma_db chroma_db.backup
cp -r models models.backup

# After reset, restore if needed
cp -r chroma_db.backup/* chroma_db/
```

---

## Getting More Help

### Information to Gather

When seeking help, include:

1. **System Info:**
   ```bash
   uname -a
   free -h
   df -h
   ```

2. **Docker Info:**
   ```bash
   docker --version
   docker-compose --version
   docker info
   ```

3. **Application Logs:**
   ```bash
   docker-compose logs --tail=200 > logs.txt
   ```

4. **Configuration:**
   - `.env` file contents (remove secrets)
   - `docker-compose.yml`
   - Steps to reproduce

### Where to Get Help

- **GitHub Issues**: https://github.com/policedbc/qwendbc/issues
- **Documentation**: Check other docs in `/docs`
- **Community**: GitHub Discussions

---

*Last updated: January 2025*
*Version: 1.0.0*

See also:
- [Getting Started](getting-started.md)
- [Chat Usage](chat-usage.md)
- [Deployment](../deployment/docker.md)
