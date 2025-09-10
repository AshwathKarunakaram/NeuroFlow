#!/usr/bin/env python3
"""
Optimized Model Manager
Handles all AI models with persistence and caching
"""

import os
import time
import torch
import kagglehub
from typing import Dict, Any, Optional, Union
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import requests
import json

from config import Config

class ModelManager:
    """Centralized model management with persistence"""
    
    def __init__(self):
        self.gemma_pipeline = None
        self.ollama_client = None
        self.is_initialized = False
        self._cache = {}
        
    def initialize(self) -> bool:
        """Initialize all models"""
        try:
            print("🚀 Initializing Model Manager...")
            
            # Initialize Gemma pipeline
            self.gemma_pipeline = GemmaPipeline()
            if not self.gemma_pipeline.load():
                return False
            
            # Initialize Ollama client
            self.ollama_client = OllamaClient()
            if not self.ollama_client.initialize():
                return False
            
            self.is_initialized = True
            print("✅ Model Manager initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error initializing Model Manager: {e}")
            return False
    
    def process_multimodal(self, image_path: Optional[str] = None, 
                          audio_path: Optional[str] = None, 
                          instruction: str = "",
                          performance_mode: bool = False) -> str:
        """Unified multimodal processing"""
        if not self.is_initialized:
            raise RuntimeError("Model Manager not initialized")
        
        # Generate cache key
        cache_key = self._generate_cache_key(image_path, audio_path, instruction, performance_mode)
        
        # Check cache first
        if Config.ENABLE_CACHING and cache_key in self._cache:
            print("📋 Using cached result")
            return self._cache[cache_key]
        
        try:
            # Process with Gemma
            if image_path and audio_path:
                result = self.gemma_pipeline.process_multimodal(image_path, audio_path, instruction)
            elif image_path:
                result = self.gemma_pipeline.process_image(image_path, instruction)
            elif audio_path:
                result = self.gemma_pipeline.process_audio(audio_path, instruction)
            else:
                result = self.ollama_client.generate_response(instruction)
            
            # Enhance with Ollama if not performance mode
            if not performance_mode and (image_path or audio_path):
                enhanced_result = self.ollama_client.enhance_analysis(result, image_path, audio_path)
                result = enhanced_result
            
            # Cache result
            if Config.ENABLE_CACHING:
                self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"❌ Error in multimodal processing: {e}")
            return f"Error processing request: {str(e)}"
    
    def generate_text_response(self, message: str, context: str = "") -> str:
        """Generate text response with context"""
        if not self.is_initialized:
            raise RuntimeError("Model Manager not initialized")
        
        # Combine message with context
        if context:
            prompt = f"Context: {context}\n\nUser: {message}\n\nAssistant:"
        else:
            prompt = message
        
        return self.ollama_client.generate_response(prompt)
    
    def _generate_cache_key(self, image_path: Optional[str], audio_path: Optional[str], 
                           instruction: str, performance_mode: bool) -> str:
        """Generate cache key for request"""
        import hashlib
        
        key_data = f"{image_path or ''}:{audio_path or ''}:{instruction}:{performance_mode}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_status(self) -> Dict[str, Any]:
        """Get model status"""
        return {
            'initialized': self.is_initialized,
            'gemma_loaded': self.gemma_pipeline.is_loaded if self.gemma_pipeline else False,
            'ollama_available': self.ollama_client.is_available() if self.ollama_client else False,
            'cache_size': len(self._cache)
        }


class GemmaPipeline:
    """Optimized Gemma 3n 2B pipeline"""
    
    def __init__(self):
        self.model_ref = Config.GEMMA_MODEL_REF
        self.device = Config.GEMMA_DEVICE
        self.torch_dtype = getattr(torch, Config.GEMMA_TORCH_DTYPE)
        self.max_tokens = Config.GEMMA_MAX_TOKENS
        self.temperature = Config.GEMMA_TEMPERATURE
        
        self.processor = None
        self.model = None
        self.is_loaded = False
    
    def load(self) -> bool:
        """Load Gemma model with persistence"""
        print("📥 Loading Gemma 3n 2B model...")
        start_time = time.time()
        
        try:
            # Check cache first
            cache_dir = os.path.expanduser("~/.cache/kagglehub/models/google/gemma-3n/transformers/gemma-3n-e2b-it/2")
            
            if os.path.exists(cache_dir):
                print(f"📁 Using cached model: {cache_dir}")
                model_path = cache_dir
            else:
                print("📥 Downloading model from Kaggle...")
                model_path = kagglehub.model_download(self.model_ref)
                print(f"✅ Model downloaded to: {model_path}")
            
            # Load processor and model
            print("🔧 Loading processor and model...")
            self.processor = AutoProcessor.from_pretrained(model_path)
            self.model = AutoModelForImageTextToText.from_pretrained(
                model_path,
                device_map=self.device,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
            )
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            load_time = time.time() - start_time
            print(f"✅ Gemma model loaded in {load_time:.2f}s")
            return True
            
        except Exception as e:
            print(f"❌ Error loading Gemma model: {e}")
            return False
    
    def process_image(self, image_path: str, instruction: str = "") -> str:
        """Process image with instruction"""
        if not self.is_loaded:
            raise RuntimeError("Gemma model not loaded")
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Create prompt
            if not instruction.strip():
                prompt = "Please describe this image in detail."
            else:
                prompt = f"Image context: {instruction}\n\nPlease analyze this image and respond to the instruction."
            
            # Create messages format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "url": image_path},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Process with model
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            prompt_len = inputs["input_ids"].shape[-1]
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            result = self.processor.batch_decode(
                outputs[:, prompt_len:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            return result.strip()
            
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            return f"Error processing image: {str(e)}"
    
    def process_audio(self, audio_path: str, instruction: str = "") -> str:
        """Process audio with instruction"""
        if not self.is_loaded:
            raise RuntimeError("Gemma model not loaded")
        
        try:
            # Create prompt
            if not instruction.strip():
                prompt = "Please transcribe this audio clearly and accurately."
            else:
                prompt = f"Audio context: {instruction}\n\nPlease analyze this audio and respond to the instruction."
            
            # Create messages format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "audio", "url": audio_path},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Process with model
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            prompt_len = inputs["input_ids"].shape[-1]
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            result = self.processor.batch_decode(
                outputs[:, prompt_len:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            return result.strip()
            
        except Exception as e:
            print(f"❌ Error processing audio: {e}")
            return f"Error processing audio: {str(e)}"
    
    def process_multimodal(self, image_path: str, audio_path: str, instruction: str = "") -> str:
        """Process both image and audio"""
        if not self.is_loaded:
            raise RuntimeError("Gemma model not loaded")
        
        try:
            # Create multimodal prompt
            prompt_parts = []
            if instruction.strip():
                prompt_parts.append(f"Instruction: {instruction}")
            
            prompt_parts.append("Please analyze the provided image and audio content.")
            
            prompt = "\n\n".join(prompt_parts)
            
            # Create messages format
            content = [
                {"type": "image", "url": image_path},
                {"type": "audio", "url": audio_path},
                {"type": "text", "text": prompt}
            ]
            
            messages = [
                {
                    "role": "user",
                    "content": content
                }
            ]
            
            # Process with model
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            prompt_len = inputs["input_ids"].shape[-1]
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            result = self.processor.batch_decode(
                outputs[:, prompt_len:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            return result.strip()
            
        except Exception as e:
            print(f"❌ Error processing multimodal: {e}")
            return f"Error processing multimodal: {str(e)}"


class OllamaClient:
    """Optimized Ollama client"""
    
    def __init__(self):
        self.base_url = Config.OLLAMA_BASE_URL
        self.model_name = Config.OLLAMA_MODEL_NAME
        self.max_tokens = Config.OLLAMA_MAX_TOKENS
        self.temperature = Config.OLLAMA_TEMPERATURE
        self.timeout = Config.OLLAMA_TIMEOUT
        
        self.session = requests.Session()
    
    def initialize(self) -> bool:
        """Initialize Ollama client"""
        try:
            print("🤖 Initializing Ollama client...")
            if self.is_available():
                print("✅ Ollama client ready")
                return True
            else:
                print("⚠️ Ollama not available, but continuing...")
                return True  # Continue without Ollama
        except Exception as e:
            print(f"⚠️ Ollama initialization warning: {e}")
            return True  # Continue without Ollama
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama"""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'No response generated')
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Ollama connection error: {e}")
            return f"Error connecting to Ollama: {str(e)}"
        except Exception as e:
            print(f"⚠️ Ollama generation error: {e}")
            return f"Error generating response: {str(e)}"
    
    def enhance_analysis(self, analysis: str, image_path: Optional[str] = None, 
                        audio_path: Optional[str] = None) -> str:
        """Enhance analysis with context"""
        try:
            context_parts = []
            if image_path:
                context_parts.append("image analysis")
            if audio_path:
                context_parts.append("audio analysis")
            
            context = " and ".join(context_parts) if context_parts else "multimodal analysis"
            
            enhancement_prompt = f"""Based on the following {context}:

{analysis}

Please provide a helpful, detailed response that builds upon this analysis. Make it educational and engaging."""
            
            return self.generate_response(enhancement_prompt)
            
        except Exception as e:
            print(f"⚠️ Error enhancing analysis: {e}")
            return analysis  # Return original if enhancement fails
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


