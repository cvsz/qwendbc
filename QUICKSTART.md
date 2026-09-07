# Quick Start Guide

## For Your Hardware (Intel Xeon E3-1225 v5, 16GB RAM, No GPU)

### Option 1: Docker (Recommended)

```bash
cd qwen-llm-app

# Copy environment file
cp configs/.env.example configs/.env

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy config
cp ../configs/.env .

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### First Use

1. Open http://localhost:3000 in your browser
2. Click "Load Model" button (this downloads ~1GB model file)
3. Wait for model to load (first time may take 2-5 minutes)
4. Start chatting!

### Performance Tips for Your System

Given your hardware specs:
- **Model**: Qwen2.5-1.5B (quantized 4-bit) - uses ~1.5GB RAM
- **Threads**: 4 (matching your CPU cores)
- **Context**: 4096 tokens (balance between memory and capability)
- **No GPU**: All inference runs on CPU

If you experience slowness:
1. Close other applications to free RAM
2. Reduce MAX_CONTEXT_LENGTH to 2048 in configs/.env
3. Consider using an even smaller model (Qwen2.5-0.5B)

### Alternative Models

For better performance on your system, try these models by changing MODEL_NAME and MODEL_FILE in configs/.env:

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| Qwen2.5-0.5B-Instruct-GGUF | ~400MB | Fastest | Basic |
| Qwen2.5-1.5B-Instruct-GGUF | ~1GB | Fast | Good |
| Qwen2.5-3B-Instruct-GGUF | ~2GB | Medium | Better |

Example for smallest model:
```
MODEL_NAME="Qwen/Qwen2.5-0.5B-Instruct-GGUF"
MODEL_FILE="qwen2.5-0.5b-instruct-q4_k_m.gguf"
```

### Troubleshooting

**Model fails to load:**
- Check available RAM (need at least 2GB free)
- Verify internet connection for initial download
- Check backend logs: `docker logs qwen-backend`

**Slow responses:**
- This is expected on CPU-only systems
- Expect 2-10 tokens/second depending on model size
- Use smaller models for faster responses

**Out of memory:**
- Close other applications
- Reduce context length in config
- Use smaller quantized model (q2_K or q3_K_M)

### API Usage Example

```bash
# Load model
curl -X POST http://localhost:8000/api/v1/model/load

# Chat completion
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'

# Check health
curl http://localhost:8000/api/v1/health
```
