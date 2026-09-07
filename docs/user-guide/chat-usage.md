# User Guide - Chat Usage

Detailed guide on using the QwenDBC chat interface effectively.

## Overview

The chat interface provides a conversational UI to interact with the Qwen language model running locally on your machine.

## Interface Components

### Status Bar

Located at the top of the interface:
- **Model Status**: Shows if model is loaded, not loaded, or error
- **Load Model Button**: Initiates model loading
- **Clear Chat Button**: Resets conversation history

### Messages Area

Main chat display showing:
- User messages (right-aligned)
- Assistant responses (left-aligned)
- Welcome message when chat is empty

### Input Area

Bottom section with:
- Text input field (multi-line)
- Send button
- Character/token count (future feature)

---

## Basic Usage

### Starting a Chat

1. **Load the Model**
   - Click "Load Model" button
   - Wait for status to show "✅ Loaded"
   - First load may take 30-60 seconds

2. **Enter Your Message**
   - Type in the text box at bottom
   - Multi-line input supported
   - Press Enter or click Send

3. **View Response**
   - Assistant response appears shortly
   - Scroll to view full conversation
   - Continue chatting as needed

### Conversation Flow

```
User: Hello! Can you help me with Python?
Assistant: Of course! I'd be happy to help with Python. What would you like to know?

User: How do I read a file?
Assistant: To read a file in Python, use the open() function:
  
  with open('filename.txt', 'r') as f:
      content = f.read()
  
The 'with' statement ensures proper file closure...

User: Thanks! What about writing?
Assistant: Writing is similar, just change the mode to 'w':
  
  with open('output.txt', 'w') as f:
      f.write('Hello, World!')
```

---

## Advanced Features

### System Messages

Set assistant behavior with system prompts:

```
System: You are a helpful coding assistant specialized in Python.
User: Write a function to calculate factorial
Assistant: [Provides Python code]
```

Note: Current UI doesn't expose system messages directly. Use API for advanced usage.

### Multi-Turn Conversations

The model maintains context within a session:

```
User: What's the capital of France?
Assistant: Paris is the capital of France.

User: What's its population?
Assistant: [Understands "its" refers to Paris]
Paris has a population of approximately 2.1 million...
```

### Clearing History

Click "Clear Chat" to:
- Remove all messages from view
- Start fresh conversation
- Reset model context

---

## Best Practices

### Writing Effective Prompts

**Be Specific:**
```
❌ Bad: "Tell me about dogs"
✅ Good: "What are the main characteristics of Golden Retrievers?"
```

**Provide Context:**
```
❌ Bad: "Fix this error"
✅ Good: "I'm getting 'IndexError: list index out of range' in this Python code: [code]"
```

**Use Step-by-Step:**
```
"Explain how to set up a React project step by step"
```

### Getting Code Help

**For Code Generation:**
```
"Write a Python function that takes a list and returns only even numbers"
```

**For Debugging:**
```
"This code isn't working: [paste code]. The error is: [error message]"
```

**For Explanation:**
```
"Explain what this regex does: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
```

### Creative Tasks

**Writing Assistance:**
```
"Help me write a professional email to request a meeting"
```

**Brainstorming:**
```
"Give me 10 ideas for a weekend project involving Raspberry Pi"
```

**Learning:**
```
"Explain quantum computing like I'm 12 years old"
```

---

## Tips & Tricks

### Response Quality

1. **Temperature Setting**: Lower (0.3-0.5) for factual, higher (0.7-0.9) for creative
2. **Max Tokens**: Adjust based on expected response length
3. **Context Length**: Longer context = better understanding but slower

### Performance Optimization

1. **Shorter Conversations**: Clear chat periodically for faster responses
2. **Specific Questions**: Focused queries get quicker answers
3. **One Topic**: Keep conversations on single topic when possible

### Error Handling

If you see errors:
1. Check model status
2. Reload model if needed
3. Simplify your query
4. Clear chat and retry

---

## Common Use Cases

### Programming Assistant

```
User: Write a REST API endpoint in FastAPI
Assistant: Here's a basic FastAPI endpoint:

from fastapi import FastAPI
app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}
```

### Data Analysis

```
User: How do I filter a pandas DataFrame for values > 10?
Assistant: Use boolean indexing:

filtered_df = df[df['column_name'] > 10]
```

### Documentation Help

```
User: Write docstring for this function
Assistant: 
"""
Calculate the factorial of a non-negative integer.

Args:
    n (int): The number to calculate factorial for
    
Returns:
    int: The factorial of n
    
Raises:
    ValueError: If n is negative
"""
```

### Language Translation

```
User: Translate "Hello, how are you?" to French
Assistant: Bonjour, comment allez-vous ?
```

### Math Problems

```
User: What's the derivative of x^2 + 3x + 5?
Assistant: The derivative is: 2x + 3
```

---

## Limitations

### Knowledge Cutoff

The model's knowledge is limited to its training data. Verify:
- Recent events may not be known
- Latest library versions might be missing
- Always verify critical information

### Context Window

Maximum context length is 4096 tokens:
- Long conversations may lose early context
- Very long documents may be truncated
- Clear chat to reset context

### Accuracy

The model may:
- Make factual errors
- Generate plausible but incorrect information
- Struggle with complex reasoning

Always verify important information from authoritative sources.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Enter | Send message |
| Shift+Enter | New line in input |
| Ctrl+C | Copy selected text |
| Ctrl+A | Select all in input |

---

## Troubleshooting

### Slow Responses

**Causes:**
- Large model size
- Limited CPU resources
- Long conversation history

**Solutions:**
- Close other applications
- Reduce max_tokens setting
- Clear chat history

### Model Won't Load

**Check:**
- Available RAM (need 8GB+)
- Internet connection (for download)
- Backend logs for errors

### Garbled Output

**Try:**
- Reloading the model
- Clearing chat history
- Using simpler prompts
- Checking temperature settings

---

## Privacy Notes

Remember:
- All processing happens locally
- No data is sent to external servers
- Chat history stored only on your device
- Clear sensitive conversations manually

---

*Last updated: January 2025*
*Version: 1.0.0*

See also:
- [Getting Started](getting-started.md)
- [Model Management](model-management.md)
- [Troubleshooting](troubleshooting.md)
