# User Guide - Getting Started

Welcome to QwenDBC! This guide will help you get up and running with your local AI chat application.

## Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** installed
- At least **8GB RAM** (16GB recommended)
- **10GB free disk space**
- Internet connection (for initial model download only)

## Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/policedbc/qwendbc.git
cd qwendbc
```

### Step 2: Configure Environment (Optional)

Create a `.env` file in the root directory to customize settings:

```bash
cp .env.example .env
```

Edit `.env` with your preferred settings:

```env
# Model Configuration
MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct-GGUF
MODEL_FILE=qwen2.5-1.5b-instruct-q4_k_m.gguf
N_THREADS=4
MAX_CONTEXT_LENGTH=4096

# Security
SECRET_KEY=your-super-secret-key-change-this

# Server
HOST=0.0.0.0
PORT=8000
```

### Step 3: Start the Application

```bash
docker-compose up -d
```

The application will:
1. Build the backend and frontend containers
2. Download the AI model (this may take several minutes)
3. Start the services

### Step 4: Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Step 5: Load the Model

1. Click the **"Load Model"** button in the web interface
2. Wait for the model to load (first time may take 30-60 seconds)
3. Status indicator will show "✅ Loaded" when ready

### Step 6: Start Chatting!

Type your message and press Enter or click "Send". The AI will respond shortly.

---

## Using the Chat Interface

### Basic Chat

1. **Type your message** in the text input at the bottom
2. **Press Enter** or click **Send** to submit
3. **Wait for response** from the AI assistant
4. **Continue conversation** by typing follow-up messages

### Conversation Tips

- Be clear and specific in your questions
- Provide context for better responses
- Use system messages to set assistant behavior
- Keep conversations focused for best results

### Example Conversations

#### Simple Question
```
User: What is the capital of France?
Assistant: The capital of France is Paris.
```

#### Creative Writing
```
User: Write a short poem about autumn
Assistant: Leaves of gold and crimson fall...
```

#### Code Help
```
User: How do I reverse a string in Python?
Assistant: You can reverse a string using slicing: reversed_string = original[::-1]
```

---

## Model Management

### Checking Model Status

The status bar at the top shows the current model state:
- **⏸️ Not Loaded** - Model needs to be loaded
- **✅ Loaded** - Model is ready for use
- **❌ Error** - There was a problem loading the model

### Loading the Model

Click the **"Load Model"** button when status shows "Not Loaded".

**Note:** First-time loading takes longer as the model downloads from HuggingFace.

### Unloading the Model

To free up memory:
1. Stop the application: `docker-compose down`
2. Or use the API: `POST /api/v1/model/unload`

### Changing Models

To use a different model:

1. Stop the application: `docker-compose down`
2. Edit `.env` file:
   ```env
   MODEL_NAME=Qwen/Qwen2.5-3B-Instruct-GGUF
   MODEL_FILE=qwen2.5-3b-instruct-q4_k_m.gguf
   ```
3. Remove old model files (optional):
   ```bash
   rm -rf models/*
   ```
4. Restart: `docker-compose up -d`

---

## Troubleshooting

### Model Won't Load

**Symptoms:** Error message or timeout when loading model

**Solutions:**
1. Check available RAM (need at least 8GB free)
2. Verify internet connection for download
3. Check backend logs: `docker-compose logs backend`
4. Try reducing context length in `.env`:
   ```env
   MAX_CONTEXT_LENGTH=2048
   ```

### Slow Response Times

**Symptoms:** Responses take too long

**Solutions:**
1. Reduce model size (use smaller quantization)
2. Decrease max tokens:
   ```env
   MAX_TOKENS=1024
   ```
3. Increase CPU threads if available:
   ```env
   N_THREADS=8
   ```

### Frontend Can't Connect

**Symptoms:** "Connection failed" or similar errors

**Solutions:**
1. Verify backend is running: `docker-compose ps`
2. Check backend logs: `docker-compose logs backend`
3. Ensure port 8000 is not in use by another service
4. Restart services: `docker-compose restart`

### Out of Memory Errors

**Symptoms:** Application crashes or shows OOM errors

**Solutions:**
1. Close other memory-intensive applications
2. Use a smaller model variant
3. Reduce context length
4. Add swap space (Linux):
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### Model Download Fails

**Symptoms:** Error downloading model from HuggingFace

**Solutions:**
1. Check internet connectivity
2. Verify HuggingFace is accessible: `curl https://huggingface.co`
3. Manually download model and place in `models/` directory
4. Check firewall/proxy settings

---

## Advanced Usage

### Using the API Directly

You can interact with the API using curl or any HTTP client:

```bash
# Load model
curl -X POST http://localhost:8000/api/v1/model/load

# Send message
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### Streaming Responses

For real-time token streaming, use the stream endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ]
  }'
```

### Clearing Chat History

Click the **"Clear Chat"** button to start a new conversation.

---

## Best Practices

### For Better Responses

1. **Be Specific**: Clear, detailed questions get better answers
2. **Provide Context**: Include relevant background information
3. **Use System Messages**: Set the assistant's role and tone
4. **Break Down Complex Tasks**: Split complex requests into steps

### For Optimal Performance

1. **Close Unused Applications**: Free up RAM for the model
2. **Use SSD Storage**: Faster model loading and inference
3. **Limit Concurrent Requests**: One conversation at a time
4. **Monitor Temperature**: Ensure adequate cooling for sustained use

### For Privacy & Security

1. **Change Secret Key**: Always update SECRET_KEY in production
2. **Restrict CORS Origins**: Limit allowed origins in production
3. **Don't Share Sensitive Data**: Remember this is a local tool
4. **Regular Updates**: Keep dependencies updated for security

---

## Next Steps

- **[Model Management Guide](model-management.md)** - Advanced model configuration
- **[Troubleshooting Guide](troubleshooting.md)** - Detailed problem solving
- **[API Reference](../api/README.md)** - Complete API documentation
- **[Development Guide](../development/setup.md)** - Contributing to QwenDBC

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review backend logs: `docker-compose logs backend`
3. Review frontend logs: `docker-compose logs frontend`
4. Search existing [GitHub Issues](https://github.com/policedbc/qwendbc/issues)
5. Open a new issue with details

---

*Last updated: January 2025*
*Version: 1.0.0*
