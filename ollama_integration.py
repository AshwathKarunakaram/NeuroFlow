#!/usr/bin/env python3
"""
Ollama Integration Module
Handles communication with Ollama API for enhanced text generation
"""

import requests
import json
import time

class OllamaIntegration:
    """Integration with Ollama API for enhanced text generation"""
    
    def __init__(self, base_url="http://localhost:11434", model_name="gemma-3n-finetune"):
        """Initialize Ollama integration"""
        self.base_url = base_url
        self.model_name = model_name
        self.session = requests.Session()
        
    def generate_response(self, prompt, max_tokens=500, temperature=0.7):
        """Generate response using Ollama API"""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'No response generated')
            
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Ollama: {str(e)}"
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def is_available(self):
        """Check if Ollama is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_models(self):
        """Get available models"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return [] 