"""
Test suite for QwenDBC Backend
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.services.llm_service import LLMService


class TestHealthEndpoint:
    """Test health check endpoints"""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test basic health endpoint"""
        response = self.client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_model_status_unloaded(self):
        """Test model status when unloaded"""
        response = self.client.get("/api/v1/model/status")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data
        assert data["model_loaded"] is False


class TestLLMService:
    """Test LLM Service functionality"""
    
    def test_singleton_pattern(self):
        """Test that LLMService follows singleton pattern"""
        with patch('app.services.llm_service.Llama') as mock_llama:
            service1 = LLMService.get_instance()
            service2 = LLMService.get_instance()
            assert service1 is service2
    
    def test_model_not_loaded_initially(self):
        """Test that model is not loaded by default"""
        with patch('app.services.llm_service.Llama'):
            service = LLMService.get_instance()
            # Reset instance for clean test
            LLMService._instance = None
            service = LLMService.get_instance()
            assert service.model is None


class TestChatRouter:
    """Test chat router endpoints"""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_chat_completion_model_not_loaded(self):
        """Test chat completion returns error when model not loaded"""
        payload = {
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False
        }
        response = self.client.post("/api/v1/chat/completions", json=payload)
        assert response.status_code in [400, 503]  # Model not loaded
    
    def test_chat_completion_invalid_payload(self):
        """Test chat completion with invalid payload"""
        payload = {"invalid_field": "test"}
        response = self.client.post("/api/v1/chat/completions", json=payload)
        assert response.status_code == 422  # Validation error


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_default_config_values(self):
        """Test default configuration values"""
        from app.schemas.config import Settings
        settings = Settings()
        assert settings.n_threads > 0
        assert settings.max_context_length > 0
    
    def test_model_file_validation(self):
        """Test model file name validation"""
        from app.schemas.config import Settings
        settings = Settings()
        assert settings.model_file.endswith('.gguf')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
