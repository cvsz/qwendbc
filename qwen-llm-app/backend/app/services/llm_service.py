import os
import logging
from pathlib import Path
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from typing import Optional, Generator, Dict, Any, List
import json
import uuid
import time

from app.schemas.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for managing LLM model loading and inference"""
    
    _instance: Optional['LLMService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = None
            cls._instance.model_path = None
            cls._instance.is_loaded = False
        return cls._instance
    
    def download_model(self) -> str:
        """Download model from HuggingFace if not exists"""
        model_dir = Path(settings.MODEL_PATH)
        model_dir.mkdir(parents=True, exist_ok=True)
        
        model_file_path = model_dir / settings.MODEL_FILE
        
        if not model_file_path.exists():
            logger.info(f"Downloading model {settings.MODEL_NAME}...")
            try:
                model_path = hf_hub_download(
                    repo_id=settings.MODEL_NAME,
                    filename=settings.MODEL_FILE,
                    local_dir=str(model_dir)
                )
                logger.info(f"Model downloaded to {model_path}")
                return model_path
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                raise
        else:
            logger.info(f"Model already exists at {model_file_path}")
            return str(model_file_path)
    
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """Load the LLM model into memory"""
        try:
            if model_path is None:
                model_path = self.download_model()
            
            logger.info(f"Loading model from {model_path}")
            
            # Optimize for CPU-only inference (important for your hardware)
            self.model = Llama(
                model_path=model_path,
                n_ctx=settings.MAX_CONTEXT_LENGTH,
                n_threads=settings.N_THREADS,
                n_batch=settings.N_BATCH,
                n_gpu_layers=0,
                use_mmap=True,
                use_mlock=False,
                verbose=settings.DEBUG
            )
            
            self.model_path = model_path
            self.is_loaded = True
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_loaded = False
            return False
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Qwen model"""
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                formatted += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                formatted += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                formatted += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        formatted += "<|im_start|>assistant\n"
        return formatted
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Generate a response from the model"""
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded")
        
        prompt = self._format_messages(messages)
        
        try:
            output = self.model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=["<|im_end|>", "<|endoftext|>"],
                echo=False
            )
            
            return {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": settings.MODEL_NAME,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": output["choices"][0]["text"].strip()
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": output["usage"]["prompt_tokens"],
                    "completion_tokens": output["usage"]["completion_tokens"],
                    "total_tokens": output["usage"]["total_tokens"]
                }
            }
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream generation results"""
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded")
        
        prompt = self._format_messages(messages)
        
        try:
            for chunk in self.model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=["<|im_end|>", "<|endoftext|>"],
                stream=True,
                echo=False
            ):
                yield {
                    "id": f"chatcmpl-{uuid.uuid4()}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": settings.MODEL_NAME,
                    "choices": [{
                        "index": 0,
                        "delta": {
                            "content": chunk["choices"][0]["text"]
                        },
                        "finish_reason": None
                    }]
                }
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            raise
    
    def unload_model(self) -> None:
        """Unload the model from memory"""
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("Model unloaded")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "name": settings.MODEL_NAME,
            "path": str(self.model_path) if self.model_path else None,
            "context_length": settings.MAX_CONTEXT_LENGTH,
            "threads": settings.N_THREADS,
            "loaded": self.is_loaded
        }


llm_service = LLMService()
