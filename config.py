#!/usr/bin/env python3
"""
NeuroFlow Configuration Management
Centralized configuration for all components
"""

import os
from typing import Dict, Any, Optional

class Config:
    """Centralized configuration management"""
    
    # Server Configuration
    HOST = os.getenv('NEUROFLOW_HOST', '0.0.0.0')
    PORT = int(os.getenv('NEUROFLOW_PORT', 5001))
    DEBUG = os.getenv('NEUROFLOW_DEBUG', 'False').lower() == 'true'
    
    # Model Configuration
    GEMMA_MODEL_REF = "google/gemma-3n/transformers/gemma-3n-e2b-it"
    GEMMA_DEVICE = os.getenv('GEMMA_DEVICE', 'cpu')
    GEMMA_TORCH_DTYPE = os.getenv('GEMMA_TORCH_DTYPE', 'float32')
    GEMMA_MAX_TOKENS = int(os.getenv('GEMMA_MAX_TOKENS', 256))
    GEMMA_TEMPERATURE = float(os.getenv('GEMMA_TEMPERATURE', 0.7))
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL_NAME = os.getenv('OLLAMA_MODEL_NAME', 'gemma3n-finetuned')
    OLLAMA_MAX_TOKENS = int(os.getenv('OLLAMA_MAX_TOKENS', 500))
    OLLAMA_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', 0.7))
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', 30))
    
    # RAG Configuration
    RAG_DATA_DIR = os.getenv('RAG_DATA_DIR', './rag_data')
    RAG_EMBEDDING_MODEL = os.getenv('RAG_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    RAG_MAX_CONTEXT_LENGTH = int(os.getenv('RAG_MAX_CONTEXT_LENGTH', 2000))
    RAG_SIMILARITY_THRESHOLD = float(os.getenv('RAG_SIMILARITY_THRESHOLD', 0.3))
    RAG_MAX_RETRIEVED_SESSIONS = int(os.getenv('RAG_MAX_RETRIEVED_SESSIONS', 5))
    
    # Performance Configuration
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'True').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 10))
    
    # File Processing Configuration
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB
    ALLOWED_IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    ALLOWED_AUDIO_TYPES = ['mp3', 'wav', 'm4a', 'mp4', 'aac', 'flac']
    TEMP_DIR = os.getenv('TEMP_DIR', '/tmp/neuroflow')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """Get model configuration"""
        return {
            'gemma': {
                'model_ref': cls.GEMMA_MODEL_REF,
                'device': cls.GEMMA_DEVICE,
                'torch_dtype': cls.GEMMA_TORCH_DTYPE,
                'max_tokens': cls.GEMMA_MAX_TOKENS,
                'temperature': cls.GEMMA_TEMPERATURE
            },
            'ollama': {
                'base_url': cls.OLLAMA_BASE_URL,
                'model_name': cls.OLLAMA_MODEL_NAME,
                'max_tokens': cls.OLLAMA_MAX_TOKENS,
                'temperature': cls.OLLAMA_TEMPERATURE,
                'timeout': cls.OLLAMA_TIMEOUT
            }
        }
    
    @classmethod
    def get_rag_config(cls) -> Dict[str, Any]:
        """Get RAG configuration"""
        return {
            'data_dir': cls.RAG_DATA_DIR,
            'embedding_model': cls.RAG_EMBEDDING_MODEL,
            'max_context_length': cls.RAG_MAX_CONTEXT_LENGTH,
            'similarity_threshold': cls.RAG_SIMILARITY_THRESHOLD,
            'max_retrieved_sessions': cls.RAG_MAX_RETRIEVED_SESSIONS
        }
    
    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        """Get server configuration"""
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'debug': cls.DEBUG
        }
