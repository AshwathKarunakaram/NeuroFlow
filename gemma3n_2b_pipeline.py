#!/usr/bin/env python3
"""
Gemma 3n 2B Pipeline
Simple and efficient multimodal processing using 2B model
"""

import torch
import time
import os
import subprocess
import hashlib
from transformers import AutoProcessor, AutoModelForImageTextToText
import kagglehub
from typing import Dict, Any

class Gemma3n2BPipeline:
    """Efficient 2B pipeline for multimodal processing"""
    
    def __init__(self):
        self.model_ref = "google/gemma-3n/transformers/gemma-3n-e2b-it"
        self.processor = None
        self.model = None
        self.is_loaded = False
        self.cache = {}
        
    def load_model(self):
        """Load the 2B model"""
        print("🚀 Loading Gemma 3n 2B model...")
        start_time = time.time()
        
        try:
            # Check if model is already cached locally
            cache_dir = os.path.expanduser("~/.cache/kagglehub/models/google/gemma-3n/transformers/gemma-3n-e2b-it/2")
            
            if os.path.exists(cache_dir):
                print(f"📁 Using locally cached model: {cache_dir}")
                model_path = cache_dir
            else:
                print("📥 Downloading 2B model from Kaggle...")
                model_path = kagglehub.model_download(self.model_ref)
                print(f"✅ Model downloaded to: {model_path}")
            
            print("🔧 Loading processor and 2B model...")
            self.processor = AutoProcessor.from_pretrained(model_path)
            self.model = AutoModelForImageTextToText.from_pretrained(
                model_path,
                device_map="cpu",
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
            )
            self.model.to("cpu")
            self.model.eval()
            
            print("✅ 2B model loaded successfully")
            self.is_loaded = True
            load_time = time.time() - start_time
            print(f"⏱️ Load time: {load_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Error loading 2B model: {e}")
            # If download fails, try to use cached version
            cache_dir = os.path.expanduser("~/.cache/kagglehub/models/google/gemma-3n/transformers/gemma-3n-e2b-it/2")
            if os.path.exists(cache_dir):
                print(f"🔄 Trying cached model: {cache_dir}")
                try:
                    model_path = cache_dir
                    self.processor = AutoProcessor.from_pretrained(model_path)
                    self.model = AutoModelForImageTextToText.from_pretrained(
                        model_path,
                        device_map="cpu",
                        torch_dtype=torch.float32,
                        low_cpu_mem_usage=True,
                    )
                    self.model.to("cpu")
                    self.model.eval()
                    
                    print("✅ 2B model loaded from cache successfully")
                    self.is_loaded = True
                    load_time = time.time() - start_time
                    print(f"⏱️ Load time: {load_time:.2f}s")
                except Exception as cache_error:
                    print(f"❌ Error loading cached model: {cache_error}")
                    raise
            else:
                raise
    
    def get_cache_key(self, task_type: str, file_path: str, prompt: str) -> str:
        """Generate cache key for request"""
        content = f"{task_type}:{file_path}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def analyze_audio_with_instruction(self, audio_path: str, instruction_context: str = "", max_tokens: int = 256) -> str:
        """Audio analysis with instruction understanding using 2B model"""
        cache_key = self.get_cache_key("audio_instruction", audio_path, instruction_context)
        if cache_key in self.cache:
            print("🎵 Using cached audio instruction analysis")
            return self.cache[cache_key]
        
        if not self.is_loaded:
            raise ValueError("2B model not loaded")
        
        print(f"🎵 2B analyzing audio with instruction: {audio_path}")
        start_time = time.time()
        
        try:
            # Enhanced prompt to understand audio instructions
            enhanced_prompt = f"""You are an intelligent AI assistant. Listen carefully to the audio content and understand any instructions or questions the user is asking.

{instruction_context}

Please:
1. First, transcribe what the user is saying in the audio
2. Identify if they are giving instructions, asking questions, or making requests
3. If they mention analyzing an image, focus on that instruction
4. If they ask a general question, provide a helpful response
5. If they give specific instructions, acknowledge and address them

Audio content:"""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "audio", "url": audio_path},
                        {"type": "text", "text": enhanced_prompt}
                    ]
                }
            ]
            
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
            
            prompt_len = inputs["input_ids"].shape[-1]
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    num_beams=1,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.0,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            analysis = self.processor.batch_decode(
                outputs[:, prompt_len:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            self.cache[cache_key] = analysis
            
            analyze_time = time.time() - start_time
            print(f"✅ 2B audio instruction analysis completed in {analyze_time:.2f}s")
            return analysis
            
        except Exception as e:
            print(f"❌ 2B audio instruction analysis error: {e}")
            return ""

    def analyze_audio(self, audio_path: str, prompt: str = "Analyze this audio content.", max_tokens: int = 256) -> str:
        """Audio analysis using 2B model with custom prompt - now uses instruction-aware approach"""
        # Use the new instruction-aware method for better audio understanding
        return self.analyze_audio_with_instruction(
            audio_path=audio_path,
            instruction_context=prompt,
            max_tokens=max_tokens
        )
    
    def analyze_image(self, image_path: str, prompt: str = "Describe this image.", max_tokens: int = 256) -> str:
        """Image analysis using 2B model with enhanced instruction understanding"""
        cache_key = self.get_cache_key("image", image_path, prompt)
        if cache_key in self.cache:
            print("🎯 Using cached image analysis")
            return self.cache[cache_key]
        
        if not self.is_loaded:
            raise ValueError("2B model not loaded")
        
        print(f"🖼️ 2B analyzing image: {image_path}")
        start_time = time.time()
        
        try:
            # Enhanced prompt for better instruction understanding
            enhanced_prompt = f"""You are an intelligent AI assistant analyzing an image. 

{prompt}

Please provide a detailed, helpful analysis that directly addresses the user's request or question."""
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "url": image_path},
                        {"type": "text", "text": enhanced_prompt}
                    ]
                }
            ]
            
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
            
            prompt_len = inputs["input_ids"].shape[-1]
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    num_beams=1,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.0,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            description = self.processor.batch_decode(
                outputs[:, prompt_len:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            self.cache[cache_key] = description
            
            analyze_time = time.time() - start_time
            print(f"✅ 2B image analysis completed in {analyze_time:.2f}s")
            return description
            
        except Exception as e:
            print(f"❌ 2B image analysis error: {e}")
            return ""
    
    def multimodal_analysis_optimized(self, image_path: str, audio_path: str, prompt: str = "Analyze both.", max_tokens: int = 512, performance_mode: bool = False) -> Dict[str, Any]:
        """Optimized multimodal analysis - processes image and audio separately for better performance"""
        cache_key = self.get_cache_key("multimodal_optimized", f"{image_path}:{audio_path}", prompt)
        if cache_key in self.cache:
            if not performance_mode:
                print("🔗 Using cached optimized multimodal analysis")
            return self.cache[cache_key]
        
        if not self.is_loaded:
            raise ValueError("2B model not loaded")
        
        if not performance_mode:
            print(f"⚡ Performing OPTIMIZED 2B multimodal analysis (separate processing)...")
        start_time = time.time()
        
        # Detailed timing tracking
        timings = {}
        
        try:
            # Process image separately with instruction context
            if not performance_mode:
                print("🖼️ Processing image with instruction context...")
            image_start = time.time()
            
            # Create instruction context for image analysis
            image_instruction = "Describe this image in detail."
            if prompt and prompt != "Analyze both.":
                # If user provided specific instructions, use them for image analysis
                if "analyze" in prompt.lower() or "describe" in prompt.lower() or "what" in prompt.lower():
                    image_instruction = f"Based on the user's request: '{prompt}', please analyze this image."
            
            image_messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "url": image_path},
                        {"type": "text", "text": image_instruction}
                    ]
                }
            ]
            
            image_inputs = self.processor.apply_chat_template(
                image_messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            image_inputs = {k: v.to("cpu") for k, v in image_inputs.items()}
            
            prompt_len = image_inputs["input_ids"].shape[-1]
            
            with torch.no_grad():
                image_outputs = self.model.generate(
                    **image_inputs, 
                    max_new_tokens=max_tokens // 2,  # Use half tokens for each
                    do_sample=True,
                    num_beams=1,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            image_analysis = self.processor.batch_decode(
                image_outputs[:, prompt_len:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            image_time = time.time() - image_start
            timings['image_processing'] = image_time
            if not performance_mode:
                print(f"✅ Image processing completed in {image_time:.2f}s")
            
            # Process audio separately with instruction understanding
            if not performance_mode:
                print("🎵 Processing audio with instruction understanding...")
            audio_start = time.time()
            
            # Create instruction context for audio analysis
            instruction_context = ""
            if prompt and prompt != "Analyze both.":
                instruction_context = f"User's instruction: {prompt}"
            
            # Use the new audio instruction analysis method
            audio_analysis = self.analyze_audio_with_instruction(
                audio_path=audio_path,
                instruction_context=instruction_context,
                max_tokens=max_tokens // 2  # Use half tokens for each
            )
            
            audio_time = time.time() - audio_start
            timings['audio_processing'] = audio_time
            if not performance_mode:
                print(f"✅ Audio processing completed in {audio_time:.2f}s")
            
            # Combine results with instruction context
            combine_start = time.time()
            
            # Create a more intelligent combined analysis
            instruction_header = ""
            if prompt and prompt != "Analyze both.":
                instruction_header = f"**User's Request:** {prompt}\n\n"
            
            combined_analysis = f"""{instruction_header}**Image Analysis:**
{image_analysis}

**Audio Analysis:**
{audio_analysis}

**Response to User's Request:**
Based on your audio instruction and the image content, here is my analysis and response to your specific request."""
            timings['result_combination'] = time.time() - combine_start
            
            total_time = time.time() - start_time
            timings['total_time'] = total_time
            
            result = {
                "analysis": combined_analysis,
                "processing_time": total_time,
                "image_time": image_time,
                "audio_time": audio_time,
                "model": "gemma3n_2b",
                "pipeline": "2B_optimized_multimodal",
                "image_analysis": image_analysis,
                "audio_analysis": audio_analysis,
                "timings": timings
            }
            
            self.cache[cache_key] = result
            
            # Print detailed timing breakdown only if not in performance mode
            if not performance_mode:
                print(f"\n📊 PIPELINE TIMING BREAKDOWN:")
                print(f"   ├─ Image Processing:    {timings['image_processing']:.2f}s")
                print(f"   ├─ Audio Processing:    {timings['audio_processing']:.2f}s")
                print(f"   ├─ Result Combination:  {timings['result_combination']:.2f}s")
                print(f"   └─ Total Pipeline Time: {timings['total_time']:.2f}s")
            
            if not performance_mode:
                print(f"✅ Optimized multimodal analysis completed in {total_time:.2f}s")
            return result
            
        except Exception as e:
            if not performance_mode:
                print(f"❌ Optimized multimodal analysis error: {e}")
            return {"error": str(e)}

    def multimodal_analysis(self, image_path: str, audio_path: str, prompt: str = "Analyze both.", max_tokens: int = 512) -> Dict[str, Any]:
        """Multimodal analysis using 2B model"""
        cache_key = self.get_cache_key("multimodal", f"{image_path}:{audio_path}", prompt)
        if cache_key in self.cache:
            print("🔗 Using cached multimodal analysis")
            return self.cache[cache_key]
        
        if not self.is_loaded:
            raise ValueError("2B model not loaded")
        
        print(f"🔗 Performing 2B multimodal analysis...")
        start_time = time.time()
        
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "url": image_path},
                        {"type": "audio", "url": audio_path},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            inputs = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            )
            inputs = {k: v.to("cpu") for k, v in inputs.items()}
            
            prompt_len = inputs["input_ids"].shape[-1]
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs, 
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    num_beams=1,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.processor.tokenizer.eos_token_id,
                )
            
            analysis = self.processor.batch_decode(
                outputs[:, prompt_len:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )[0]
            
            total_time = time.time() - start_time
            result = {
                "analysis": analysis,
                "processing_time": total_time,
                "model": "gemma3n_2b",
                "pipeline": "2B_multimodal"
            }
            
            self.cache[cache_key] = result
            
            print(f"✅ 2B multimodal analysis completed in {total_time:.2f}s")
            return result
            
        except Exception as e:
            print(f"❌ 2B multimodal analysis error: {e}")
            return {"error": str(e)}

class OllamaIntegration:
    """Ollama integration for text generation"""
    
    def __init__(self, model_name: str = "gemma3n:e2b-it-q4_K_M", custom_model: str = None):
        self.model_name = model_name
        self.custom_model = custom_model or "gemma3n-finetuned"  # Your fine-tuned model
    
    def generate_text(self, prompt: str, max_tokens: int = 256, performance_mode: bool = False) -> str:
        """Generate text using Ollama with fine-tuned model"""
        try:
            # Always try fine-tuned model first, then fallback
            models_to_try = []
            if self.custom_model:
                models_to_try.append(self.custom_model)
            models_to_try.append(self.model_name)
            
            for model in models_to_try:
                try:
                    if not performance_mode:
                        if model == self.custom_model:
                            print(f"🎯 Using FINE-TUNED model: {model}")
                        else:
                            print(f"🔄 Fallback to model: {model}")
                        
                    cmd = [
                        "/opt/homebrew/bin/ollama", "run", model,
                        prompt
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        if not performance_mode:
                            if model == self.custom_model:
                                print(f"✅ FINE-TUNED model success: {model}")
                            else:
                                print(f"✅ Fallback model success: {model}")
                        return result.stdout.strip()
                    else:
                        if not performance_mode:
                            print(f"❌ Model {model} failed: {result.stderr}")
                        continue
                        
                except subprocess.TimeoutExpired:
                    if not performance_mode:
                        print(f"⏰ Model {model} timed out")
                    continue
                except Exception as e:
                    if not performance_mode:
                        print(f"❌ Error with model {model}: {e}")
                    continue
            
            if not performance_mode:
                print("❌ All models failed")
            return ""
                
        except Exception as e:
            if not performance_mode:
                print(f"❌ Ollama integration error: {e}")
            return "" 