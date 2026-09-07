import threading
import time
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

from huggingface_hub import hf_hub_download
from llama_cpp import Llama

from app.schemas.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Thread-safe singleton for model download, loading, and inference."""

    _instance: "LLMService | None" = None
    _lock = threading.RLock()
    model: Llama | None
    model_path: str | None
    is_loaded: bool
    _inference_lock: Any

    def __new__(cls) -> "LLMService":
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance.model = None
                instance.model_path = None
                instance.is_loaded = False
                instance._inference_lock = threading.RLock()
                cls._instance = instance
        assert cls._instance is not None
        return cls._instance

    @classmethod
    def get_instance(cls) -> "LLMService":
        return cls()

    def download_model(self) -> str:
        model_dir = Path(settings.MODEL_PATH)
        model_dir.mkdir(parents=True, exist_ok=True)
        model_file_path = model_dir / settings.MODEL_FILE

        if model_file_path.exists():
            logger.info("Model already exists at %s", model_file_path)
            return str(model_file_path)

        logger.info("Downloading model %s", settings.MODEL_NAME)
        model_path = hf_hub_download(
            repo_id=settings.MODEL_NAME,
            filename=settings.MODEL_FILE,
            local_dir=str(model_dir),
        )
        logger.info("Model downloaded to %s", model_path)
        return model_path

    def load_model(self, model_path: str | None = None) -> bool:
        with self._lock:
            if self.is_loaded and self.model is not None:
                return True

            try:
                resolved_path = model_path or self.download_model()
                logger.info("Loading model from %s", resolved_path)
                model = Llama(
                    model_path=resolved_path,
                    n_ctx=settings.MAX_CONTEXT_LENGTH,
                    n_threads=settings.N_THREADS,
                    n_batch=settings.N_BATCH,
                    n_gpu_layers=0,
                    use_mmap=True,
                    use_mlock=False,
                    verbose=settings.DEBUG,
                )
                self.model = model
                self.model_path = resolved_path
                self.is_loaded = True
                logger.info("Model loaded successfully")
                return True
            except Exception:
                self.model = None
                self.model_path = None
                self.is_loaded = False
                logger.exception("Failed to load model")
                return False

    @staticmethod
    def _format_messages(messages: list[dict[str, str]]) -> str:
        formatted_parts: list[str] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if role not in {"system", "user", "assistant"}:
                raise ValueError(f"Unsupported chat role: {role!r}")
            formatted_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")
        formatted_parts.append("<|im_start|>assistant\n")
        return "".join(formatted_parts)

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded")

        prompt = self._format_messages(messages)
        with self._inference_lock:
            try:
                output = self.model(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=["<|im_end|>", "<|endoftext|>"],
                    echo=False,
                )
                usage = output.get("usage", {})
                return {
                    "id": f"chatcmpl-{uuid.uuid4().hex}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": settings.MODEL_NAME,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": output["choices"][0]["text"].strip(),
                            },
                            "finish_reason": output["choices"][0].get("finish_reason") or "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
                        "completion_tokens": int(usage.get("completion_tokens", 0)),
                        "total_tokens": int(usage.get("total_tokens", 0)),
                    },
                }
            except Exception:
                logger.exception("Generation failed")
                raise

    def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048,
    ) -> Generator[dict[str, Any], None, None]:
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded")

        prompt = self._format_messages(messages)
        completion_id = f"chatcmpl-{uuid.uuid4().hex}"
        created_time = int(time.time())

        with self._inference_lock:
            try:
                for chunk in self.model(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=["<|im_end|>", "<|endoftext|>"],
                    stream=True,
                    echo=False,
                ):
                    choice = chunk["choices"][0]
                    text = choice.get("text", "")
                    if text:
                        yield {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": settings.MODEL_NAME,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": text},
                                    "finish_reason": None,
                                }
                            ],
                        }
                yield {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.MODEL_NAME,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
            except Exception:
                logger.exception("Stream generation failed")
                raise

    def unload_model(self) -> None:
        # Do not close llama.cpp while another thread is generating tokens.
        with self._inference_lock:
            with self._lock:
                model = self.model
                self.model = None
                self.model_path = None
                self.is_loaded = False
                if model is not None:
                    close = getattr(model, "close", None)
                    if callable(close):
                        close()
                    logger.info("Model unloaded")

    def get_model_info(self) -> dict[str, Any]:
        return {
            "name": settings.MODEL_NAME,
            "path": str(self.model_path) if self.model_path else None,
            "context_length": settings.MAX_CONTEXT_LENGTH,
            "threads": settings.N_THREADS,
            "loaded": self.is_loaded,
        }


llm_service = LLMService()
