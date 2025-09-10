#!/usr/bin/env python3
"""
Gemma 3n 2B Flask App with Offline RAG
Simple and efficient multimodal processing server with session memory
"""

import os
import json
import time
import re
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
warnings.filterwarnings("ignore")

from gemma3n_2b_pipeline import Gemma3n2BPipeline, OllamaIntegration
from core.rag_system import initialize_rag, get_rag_system

app = Flask(__name__)
CORS(app)

# Global variables
gemma3n_2b_pipeline = None
ollama_integration = None
rag_system = None

# Session management
current_session = {
    "session_id": None,
    "start_time": None,
    "uploads": [],
    "interactions": [],
    "topics": [],
    "memory_context": ""
}

def initialize_models():
    """Initialize Gemma 3n 2B, Ollama, and RAG models"""
    global gemma3n_2b_pipeline, ollama_integration, rag_system
    
    print("🚀 Initializing complete system...")
    
    try:
        # Initialize 2B pipeline
        print("📥 Loading Gemma 3n 2B model...")
        gemma3n_2b_pipeline = Gemma3n2BPipeline()
        gemma3n_2b_pipeline.load_model()
        print("✅ 2B pipeline loaded")
        
        # Initialize Ollama integration
        print("🤖 Initializing Ollama integration...")
        ollama_integration = OllamaIntegration(custom_model="gemma3n-finetuned")
        print("✅ Ollama integration ready with fine-tuned model: gemma3n-finetuned")
        
        # Initialize RAG system
        print("🧠 Initializing RAG system...")
        if initialize_rag():
            rag_system = get_rag_system()
            print("✅ RAG system ready")
        else:
            print("❌ RAG system failed to initialize")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing models: {e}")
        return False

def start_new_session():
    """Start a new session"""
    global current_session
    
    # Store previous session if exists
    if current_session["session_id"] and len(current_session["interactions"]) > 0:
        store_current_session()
    
    # Initialize new session
    session_id = str(uuid.uuid4())
    current_session.update({
        "session_id": session_id,
        "start_time": time.time(),
        "uploads": [],
        "interactions": [],
        "topics": [],
        "memory_context": ""
    })
    
    print(f"🆕 New session started: {session_id}")

def store_current_session():
    """Store current session in RAG system with Gemma-generated summary"""
    global rag_system
    
    # Ensure RAG system is initialized
    if not rag_system:
        print("🔧 RAG system not initialized, initializing now...")
        if initialize_rag():
            rag_system = get_rag_system()
            print("✅ RAG system initialized")
        else:
            print("❌ Failed to initialize RAG system")
            return
    
    if not current_session["session_id"]:
        print("⚠️ No session ID to store")
        return
    
    try:
        # Calculate session duration
        duration_minutes = (time.time() - current_session["start_time"]) / 60
        
        # Generate conversation text for summary
        interactions = current_session["interactions"]
        if interactions and gemma3n_2b_pipeline:
            try:
                # Create conversation text
                conversation_parts = []
                for interaction in interactions:
                    user_input = interaction.get('user_input', 'N/A')
                    bot_response = interaction.get('bot_response', 'N/A')
                    # Truncate very long responses
                    if len(bot_response) > 500:
                        bot_response = bot_response[:500] + "..."
                    conversation_parts.append(f"User: {user_input}")
                    conversation_parts.append(f"Assistant: {bot_response}")
                
                conversation_text = "\n\n".join(conversation_parts)
                
                # Count modalities
                image_count = len([u for u in current_session["uploads"] if u.get('type') == 'image'])
                audio_count = len([u for u in current_session["uploads"] if u.get('type') == 'audio'])
                
                # Create summary prompt for Gemma
                summary_prompt = f"""Please create a comprehensive summary of this learning session:

Session Context:
- Images uploaded: {image_count}
- Audio files uploaded: {audio_count}
- Total interactions: {len(interactions)}

Conversation:
{conversation_text}

Please provide a structured summary that includes:
1. Main topics and concepts discussed
2. Key insights and learning points
3. Questions asked and answers provided
4. Overall session focus and educational value

Make the summary detailed enough to be useful for future reference and context retrieval. Keep it to 2-3 paragraphs."""

                # Generate summary using Ollama (text generation)
                print("🧠 Ollama: Generating session summary...")
                try:
                    gemma_summary = ollama_integration.generate_text(summary_prompt, max_tokens=512)
                    if gemma_summary:
                        print("✅ Ollama: Session summary generated")
                    else:
                        print("⚠️ Ollama: Summary generation failed, using fallback")
                        gemma_summary = None
                except Exception as e:
                    print(f"⚠️ Ollama summary error: {e}")
                    gemma_summary = None
                    
            except Exception as e:
                print(f"⚠️ Error generating Gemma summary: {e}")
                gemma_summary = None
        else:
            gemma_summary = None
        
        session_data = {
            "session_id": current_session["session_id"],
            "start_time": current_session["start_time"],
            "end_time": time.time(),
            "uploads": current_session["uploads"],
            "interactions": current_session["interactions"],
            "topics": current_session["topics"],
            "duration_minutes": duration_minutes,
            "memory_context": current_session["memory_context"],
            "gemma_summary": gemma_summary  # Add Gemma-generated summary
        }
        
        # Store in RAG system
        rag_system.store_session(session_data)
        print(f"💾 Session stored: {current_session['session_id']}")
        
    except Exception as e:
        print(f"❌ Error storing session: {e}")

def analyze_with_2b_optimized(image_path, audio_path, user_query="", performance_mode=False):
    """Optimized analysis using 2B pipeline with separate processing for better performance"""
    global gemma3n_2b_pipeline
    
    # Ensure pipeline is initialized
    if not gemma3n_2b_pipeline:
        if not performance_mode:
            print("🔧 2B pipeline not initialized, initializing now...")
        try:
            from gemma3n_2b_pipeline import Gemma3n2BPipeline
            gemma3n_2b_pipeline = Gemma3n2BPipeline()
            gemma3n_2b_pipeline.load_model()
            if not performance_mode:
                print("✅ 2B pipeline initialized")
        except Exception as e:
            if not performance_mode:
                print(f"❌ Failed to initialize 2B pipeline: {e}")
            return None
    
    try:
        if not performance_mode:
            print("⚡ 2B OPTIMIZED: Starting separate multimodal analysis...")
        
        # Create enhanced prompt with memory context
        base_prompt = "Provide a comprehensive educational analysis of this image and audio combination."
        
        if current_session["memory_context"]:
            enhanced_prompt = f"{current_session['memory_context']}\n\n{base_prompt}"
        else:
            enhanced_prompt = base_prompt
        
        if user_query:
            enhanced_prompt += f"\n\nUser question: {user_query}"
        
        result = gemma3n_2b_pipeline.multimodal_analysis_optimized(
            image_path=image_path,
            audio_path=audio_path,
            prompt=enhanced_prompt,
            max_tokens=512,
            performance_mode=performance_mode
        )
        
        if result and "analysis" in result:
            if not performance_mode:
                print("✅ 2B OPTIMIZED: Separate multimodal analysis completed")
                print(f"   ├─ Image time: {result.get('image_time', 0):.2f}s")
                print(f"   └─ Audio time: {result.get('audio_time', 0):.2f}s")
            return result["analysis"]
        else:
            if not performance_mode:
                print("❌ 2B OPTIMIZED: Analysis failed")
            return None
            
    except Exception as e:
        if not performance_mode:
            print(f"❌ 2B OPTIMIZED: Error during analysis: {e}")
        return None

def analyze_with_2b(image_path, audio_path, user_query=""):
    """Analyze using 2B pipeline with memory context"""
    global gemma3n_2b_pipeline
    
    # Ensure pipeline is initialized
    if not gemma3n_2b_pipeline:
        print("🔧 2B pipeline not initialized, initializing now...")
        try:
            from gemma3n_2b_pipeline import Gemma3n2BPipeline
            gemma3n_2b_pipeline = Gemma3n2BPipeline()
            gemma3n_2b_pipeline.load_model()
            print("✅ 2B pipeline initialized")
        except Exception as e:
            print(f"❌ Failed to initialize 2B pipeline: {e}")
            return None
    
    try:
        print("🔗 2B: Starting multimodal analysis...")
        
        # Create enhanced prompt with memory context
        base_prompt = "Provide a comprehensive educational analysis of this image and audio combination."
        
        if current_session["memory_context"]:
            enhanced_prompt = f"{current_session['memory_context']}\n\n{base_prompt}"
        else:
            enhanced_prompt = base_prompt
        
        if user_query:
            enhanced_prompt += f"\n\nUser question: {user_query}"
        
        result = gemma3n_2b_pipeline.multimodal_analysis(
            image_path=image_path,
            audio_path=audio_path,
            prompt=enhanced_prompt,
            max_tokens=512
        )
        
        if result and "analysis" in result:
            print("✅ 2B: Multimodal analysis completed")
            return result["analysis"]
        else:
            print("❌ 2B: Analysis failed")
            return None
            
    except Exception as e:
        print(f"❌ 2B: Error during analysis: {e}")
        return None

def enhance_with_ollama(analysis, image_path, audio_path, performance_mode=False):
    """Enhance analysis with Ollama for better text generation with RAG and session context"""
    if not ollama_integration:
        if not performance_mode:
            print("❌ Ollama integration not available")
        return analysis
    
    try:
        if not performance_mode:
            print("🤖 Ollama: Enhancing analysis with RAG and context...")
        
        # Build context from recent interactions
        context_parts = []
        
        # Add RAG memory context if available
        if rag_system and current_session.get("memory_context"):
            if not performance_mode:
                print("🧠 Retrieving RAG context for multimodal analysis...")
            rag_context = rag_system.create_memory_context(analysis[:100])  # Use first 100 chars as query
            if rag_context:
                context_parts.append(f"RAG Memory Context:\n{rag_context}")
                if not performance_mode:
                    print("✅ RAG context retrieved for multimodal")
            elif current_session.get("memory_context"):
                context_parts.append(f"Session Context: {current_session['memory_context']}")
        
        # Add recent conversation history (last 2 interactions = 4 messages)
        recent_interactions = current_session.get("interactions", [])[-2:]
        if recent_interactions:
            context_parts.append("Recent Conversation:")
            for interaction in recent_interactions:
                user_input = interaction.get('user_input', '').strip()
                bot_response = interaction.get('bot_response', '').strip()
                if user_input:
                    context_parts.append(f"User: {user_input}")
                if bot_response:
                    # Truncate very long responses for context
                    if len(bot_response) > 200:
                        bot_response = bot_response[:200] + "..."
                    context_parts.append(f"Assistant: {bot_response}")
        
        context_text = "\n\n".join(context_parts) if context_parts else ""
        
        enhanced_prompt = f"""Based on this multimodal analysis, provide a clear, educational response that maintains conversation context and builds on past learning:

{context_text}

Multimodal Analysis:
{analysis}

Instructions:
1. If RAG context is provided, connect this analysis to past learning sessions
2. If this builds on previous conversation, reference it appropriately
3. If the user asked for specific examples or follow-ups, address those
4. Provide:
   - A concise summary (1 paragraph)
   - Key educational insights
   - Practical applications or next steps
5. Keep it helpful and engaging for a student
6. Maintain continuity with previous interactions and past sessions

Please provide a contextual, educational response:"""
        
        enhanced_response = ollama_integration.generate_text(enhanced_prompt, max_tokens=256, performance_mode=performance_mode)
        
        if enhanced_response:
            if not performance_mode:
                print("✅ Ollama: Enhancement completed with RAG and context")
            return enhanced_response
        else:
            if not performance_mode:
                print("⚠️ Ollama: Enhancement failed, using original analysis")
            return analysis
            
    except Exception as e:
        if not performance_mode:
            print(f"❌ Ollama: Error during enhancement: {e}")
        return analysis

def process_text_chat_with_prompt(message, session_id, enhanced_prompt):
    """Process text-only chat with Ollama using a pre-built prompt"""
    if not ollama_integration:
        print("❌ Ollama integration not available")
        return "I apologize, but the text chat service is currently unavailable."
    
    try:
        print("💬 Processing text chat with enhanced prompt...")
        
        # Generate response with Ollama using the provided prompt
        response = ollama_integration.generate_text(enhanced_prompt, max_tokens=256)
        
        if response:
            print("✅ Text chat response generated with memory context")
            return response
        else:
            print("⚠️ Text chat failed, using fallback")
            return f"I understand you said: \"{message}\". This is a text-only conversation. You can also upload images and audio for multimodal analysis."
            
    except Exception as e:
        print(f"❌ Error in text chat: {e}")
        return "I apologize, but I encountered an error processing your message. Please try again."

def process_text_chat(message, session_id):
    """Process text-only chat with Ollama - WITH RAG AND CONVERSATIONAL CONTEXT"""
    if not ollama_integration:
        print("❌ Ollama integration not available")
        return "I apologize, but the text chat service is currently unavailable."
    
    try:
        print("💬 Processing text chat with RAG and context...")
        
        # Check if user is asking about past sessions or using search command
        past_keywords = ['past', 'previous', 'before', 'last session', 'earlier', 'history', 'remember', 'what did we']
        is_asking_about_past = any(keyword in message.lower() for keyword in past_keywords)
        
        # Check for search command pattern: "search _____"
        search_pattern = r'^search\s+(.+)$'
        search_match = re.match(search_pattern, message.lower())
        is_search_command = search_match is not None
        
        # Extract search query if it's a search command
        search_query = None
        if is_search_command:
            search_query = search_match.group(1).strip()
            print(f"🔍 Search command detected: '{search_query}'")
        
        # Build conversational context from recent interactions
        context_parts = []
        
        # Add RAG memory context if asking about past, using search command, or if available
        if is_asking_about_past or is_search_command or current_session.get("memory_context"):
            if rag_system:
                print("🧠 Retrieving RAG context...")
                # Use search query if it's a search command, otherwise use the full message
                search_text = search_query if is_search_command else message
                rag_context = rag_system.create_memory_context(search_text)
                if rag_context:
                    context_parts.append(f"RAG Memory Context:\n{rag_context}")
                    print("✅ RAG context retrieved")
                else:
                    print("⚠️ No RAG context found")
            elif current_session.get("memory_context"):
                context_parts.append(f"Session Context: {current_session['memory_context']}")
        
        # Add recent conversation history (last 4 interactions = 8 messages)
        recent_interactions = current_session.get("interactions", [])[-4:]
        if recent_interactions:
            context_parts.append("Recent Conversation:")
            for interaction in recent_interactions:
                user_input = interaction.get('user_input', '').strip()
                bot_response = interaction.get('bot_response', '').strip()
                if user_input:
                    context_parts.append(f"User: {user_input}")
                if bot_response:
                    # Truncate very long responses for context
                    if len(bot_response) > 300:
                        bot_response = bot_response[:300] + "..."
                    context_parts.append(f"Assistant: {bot_response}")
        
        # Build the full prompt with context
        context_text = "\n\n".join(context_parts) if context_parts else ""
        
        # Enhanced prompt based on whether user is asking about past or using search
        if is_search_command:
            prompt = f"""You are Neuroflow, an intelligent AI tutor assistant. The user is searching for specific content in their learning history.

{context_text}

Search Query: "{search_query}"
Original Message: {message}

Instructions:
1. If RAG context is found, present the relevant past sessions clearly
2. Show the session dates and key learning points
3. Ask if they want to continue from any of these sessions
4. If no relevant sessions found, suggest starting fresh
5. Keep it conversational and helpful

Please provide a helpful response:"""
        elif is_asking_about_past:
            prompt = f"""You are Neuroflow, an intelligent AI tutor assistant. The user is asking about past sessions or previous learning.

{context_text}

Current User Message: {message}

Instructions:
1. If RAG context is provided, reference specific past sessions and topics
2. Remind the user what they learned in previous sessions
3. Connect current conversation to past learning
4. If no past context is found, acknowledge that and offer to start fresh
5. Be specific about what was discussed in previous sessions
6. Help the user continue their learning journey

Please provide a helpful response that connects to their learning history:"""
        else:
            prompt = f"""You are Neuroflow, an intelligent AI tutor assistant. Maintain context and provide helpful, educational responses.

{context_text}

Current User Message: {message}

Instructions:
1. If this is a follow-up question, reference the previous conversation
2. If this is about uploaded content (images/audio), acknowledge that context
3. Provide helpful, educational responses that build on previous interactions
4. Keep responses concise but informative
5. If the user asks for examples related to previous topics, provide relevant examples

Please provide a contextual, helpful response:"""
        
        # Generate response with Ollama
        response = ollama_integration.generate_text(prompt, max_tokens=256)
        
        if response:
            print("✅ Text chat response generated with RAG and context")
            return response
        else:
            print("⚠️ Text chat failed, using fallback")
            return f"I understand you said: \"{message}\". This is a text-only conversation. You can also upload images and audio for multimodal analysis."
            
    except Exception as e:
        print(f"❌ Error in text chat: {e}")
        return "I apologize, but I encountered an error processing your message. Please try again."

def process_files_2b_optimized(image_path, audio_path, user_query="", performance_mode=False):
    """2B optimized multimodal processing with separate processing for better performance"""
    if not performance_mode:
        print("⚡ 2B OPTIMIZED processing started...")
    start_time = time.time()
    
    # Detailed timing tracking
    timings = {}
    
    try:
        # Ensure session is started
        if not current_session["session_id"]:
            current_session["session_id"] = f"session_{int(time.time())}"
        
        # Add uploads to session
        current_session["uploads"].append({
            "type": "image",
            "path": image_path,
            "timestamp": time.time()
        })
        current_session["uploads"].append({
            "type": "audio", 
            "path": audio_path,
            "timestamp": time.time()
        })
        
        # Process with 2B optimized (separate processing)
        if not performance_mode:
            print("🔍 Starting 2B optimized analysis...")
        analysis_start = time.time()
        gemma3n_analysis = analyze_with_2b_optimized(image_path, audio_path, user_query, performance_mode)
        timings['2b_analysis'] = time.time() - analysis_start
        
        if gemma3n_analysis:
            # Enhance with Ollama
            if not performance_mode:
                print("🤖 Starting Ollama enhancement...")
            ollama_start = time.time()
            final_response = enhance_with_ollama(gemma3n_analysis, image_path, audio_path, performance_mode)
            timings['ollama_enhancement'] = time.time() - ollama_start
            
            # Add interaction to session
            session_start = time.time()
            current_session["interactions"].append({
                "timestamp": time.time(),
                "user_input": user_query or "Optimized multimodal upload",
                "bot_response": final_response,
                "processing_time": time.time() - start_time
            })
            timings['session_management'] = time.time() - session_start
            
            total_time = time.time() - start_time
            timings['total_time'] = total_time
            
            # Print detailed timing breakdown only if not in performance mode
            if not performance_mode:
                print(f"\n📊 DETAILED TIMING BREAKDOWN:")
                print(f"   ├─ 2B Analysis:        {timings['2b_analysis']:.2f}s")
                print(f"   ├─ Ollama Enhancement: {timings['ollama_enhancement']:.2f}s")
                print(f"   ├─ Session Management: {timings['session_management']:.2f}s")
                print(f"   └─ Total Time:         {timings['total_time']:.2f}s")
            
            if not performance_mode:
                print(f"✅ 2B OPTIMIZED processing completed in {total_time:.2f}s")
            return {
                "response": final_response,
                "completion_time": datetime.now().isoformat()
            }
            
        else:
            if not performance_mode:
                print("❌ 2B optimized analysis failed")
            return {
                "response": "Analysis failed. Please try again.",
                "completion_time": datetime.now().isoformat()
            }
            
    except Exception as e:
        if not performance_mode:
            print(f"❌ 2B OPTIMIZED processing error: {e}")
        return {
            "response": f"Processing error: {str(e)}",
            "completion_time": datetime.now().isoformat()
        }

def process_files_2b(image_path, audio_path, user_query=""):
    """2B multimodal processing with session tracking"""
    print("🔄 2B processing started...")
    start_time = time.time()
    
    try:
        # Ensure session is started
        if not current_session["session_id"]:
            current_session["session_id"] = f"session_{int(time.time())}"
        
        # Add uploads to session
        current_session["uploads"].append({
            "type": "image",
            "path": image_path,
            "timestamp": time.time()
        })
        current_session["uploads"].append({
            "type": "audio", 
            "path": audio_path,
            "timestamp": time.time()
        })
        
        # Process with 2B
        gemma3n_analysis = analyze_with_2b(image_path, audio_path, user_query)
        
        if gemma3n_analysis:
            final_response = enhance_with_ollama(gemma3n_analysis, image_path, audio_path)
            
            # Add interaction to session
            current_session["interactions"].append({
                "timestamp": time.time(),
                "user_input": user_query or "Multimodal upload",
                "bot_response": final_response,
                "processing_time": time.time() - start_time
            })
            
            print(f"✅ 2B processing completed in {time.time() - start_time:.2f}s")
            return final_response
            
        else:
            print("❌ 2B analysis failed")
            return "Analysis failed. Please try again."
            
    except Exception as e:
        print(f"❌ 2B processing error: {e}")
        return f"Processing error: {str(e)}"

@app.route('/')
def home():
    return jsonify({
        "status": "Gemma 3n 2B Flask server with RAG running", 
        "pipeline": "gemma3n_2b_optimized_with_rag",
        "features": ["2B audio transcription", "2B image analysis", "2B optimized multimodal analysis", "Ollama enhancement", "Offline RAG memory", "Session management", "Text chat"]
    })

@app.route('/process', methods=['POST'])
def process():
    """2B multimodal processing endpoint with session tracking - supports image OR audio"""
    print("🔄 2B Flask: Processing request started")
    
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        audio_path = data.get('audio_path')
        user_query = data.get('user_query', '')
        
        print(f"📋 2B Flask: File paths received - Image: {image_path}, Audio: {audio_path}")
        if user_query:
            print(f"📝 2B Flask: User query - {user_query}")
        
        # Check if at least one file exists
        has_image = image_path and os.path.exists(image_path)
        has_audio = audio_path and os.path.exists(audio_path)
        
        if not has_image and not has_audio:
            print("❌ 2B Flask: No valid files provided")
            return jsonify({"error": "At least one image or audio file is required"}), 400
        
        print(f"🔧 2B Flask: Image exists: {has_image}")
        print(f"🔧 2B Flask: Audio exists: {has_audio}")
        
        # Handle different processing modes
        if has_image and has_audio:
            # Optimized multimodal analysis (separate processing for better performance)
            print("⚡ Using optimized separate processing for image+audio (performance mode)")
            result = process_files_2b_optimized(image_path, audio_path, user_query, performance_mode=True)
            response = result["response"]
            completion_time = result["completion_time"]
        elif has_image:
            # Image-only analysis
            response = process_image_only(image_path, user_query)
            completion_time = datetime.now().isoformat()
        elif has_audio:
            # Audio-only analysis
            response = process_audio_only(audio_path, user_query)
            completion_time = datetime.now().isoformat()
        else:
            response = "Error: No valid files to process"
            completion_time = datetime.now().isoformat()
        
        # Clean up files
        if has_image:
            try:
                os.remove(image_path)
                print(f"🗑️ 2B Flask: Deleted image file: {image_path}")
            except:
                pass
        
        if has_audio:
            try:
                os.remove(audio_path)
                print(f"🗑️ 2B Flask: Deleted audio file: {audio_path}")
            except:
                pass
        
        print("✅ 2B Flask: Processing completed successfully")
        return jsonify({
            "response": response,
            "completion_time": completion_time
        })
        
    except Exception as e:
        print(f"❌ 2B Flask: Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

def process_image_only(image_path, user_query=""):
    """Process image-only analysis"""
    print("🖼️ Processing image-only analysis...")
    start_time = time.time()
    
    try:
        # Ensure session is started
        if not current_session["session_id"]:
            current_session["session_id"] = f"session_{int(time.time())}"
        
        # Add upload to session
        current_session["uploads"].append({
            "type": "image",
            "path": image_path,
            "timestamp": time.time()
        })
        
        # Create enhanced prompt with memory context
        base_prompt = "Provide a comprehensive analysis of this image."
        
        if current_session["memory_context"]:
            enhanced_prompt = f"{current_session['memory_context']}\n\n{base_prompt}"
        else:
            enhanced_prompt = base_prompt
        
        if user_query:
            enhanced_prompt += f"\n\nUser question: {user_query}"
        
        # Process with 2B
        if gemma3n_2b_pipeline:
            result = gemma3n_2b_pipeline.analyze_image(
                image_path=image_path,
                prompt=enhanced_prompt,
                max_tokens=512
            )
            
            if result and isinstance(result, str):
                # analyze_image returns a string directly
                analysis = result
                final_response = enhance_with_ollama(analysis, image_path, None)
                
                # Add interaction to session
                current_session["interactions"].append({
                    "timestamp": time.time(),
                    "user_input": user_query or "Image upload",
                    "bot_response": final_response,
                    "processing_time": time.time() - start_time
                })
                
                print(f"✅ Image-only processing completed in {time.time() - start_time:.2f}s")
                return final_response
            else:
                return "Image analysis failed. Please try again."
        else:
            return "Image analysis service not available."
            
    except Exception as e:
        print(f"❌ Image-only processing error: {e}")
        return f"Image processing error: {str(e)}"

def process_audio_only(audio_path, user_query=""):
    """Process audio-only analysis"""
    print("🎵 Processing audio-only analysis...")
    start_time = time.time()
    
    try:
        # Ensure session is started
        if not current_session["session_id"]:
            current_session["session_id"] = f"session_{int(time.time())}"
        
        # Add upload to session
        current_session["uploads"].append({
            "type": "audio",
            "path": audio_path,
            "timestamp": time.time()
        })
        
        # Create enhanced prompt with memory context
        base_prompt = "Provide a comprehensive analysis of this audio content."
        
        if current_session["memory_context"]:
            enhanced_prompt = f"{current_session['memory_context']}\n\n{base_prompt}"
        else:
            enhanced_prompt = base_prompt
        
        if user_query:
            enhanced_prompt += f"\n\nUser question: {user_query}"
        
        # Process with 2B - ensure pipeline is initialized
        global gemma3n_2b_pipeline
        if not gemma3n_2b_pipeline:
            print("🔧 2B pipeline not initialized, initializing now...")
            try:
                from gemma3n_2b_pipeline import Gemma3n2BPipeline
                gemma3n_2b_pipeline = Gemma3n2BPipeline()
                gemma3n_2b_pipeline.load_model()
                print("✅ 2B pipeline initialized")
            except Exception as e:
                print(f"❌ Failed to initialize 2B pipeline: {e}")
                return "Audio analysis service not available - model initialization failed."
        
        if gemma3n_2b_pipeline:
            result = gemma3n_2b_pipeline.analyze_audio(
                audio_path=audio_path,
                prompt=enhanced_prompt,
                max_tokens=512
            )
            
            if result and isinstance(result, str):
                # analyze_audio returns a string directly
                analysis = result
                # Try to enhance with Ollama, fallback to direct analysis if not available
                try:
                    final_response = enhance_with_ollama(analysis, None, audio_path)
                except Exception as e:
                    print(f"⚠️ Ollama enhancement not available: {e}")
                    final_response = analysis
                
                # Add interaction to session
                current_session["interactions"].append({
                    "timestamp": time.time(),
                    "user_input": user_query or "Audio upload",
                    "bot_response": final_response,
                    "processing_time": time.time() - start_time
                })
                
                print(f"✅ Audio-only processing completed in {time.time() - start_time:.2f}s")
                return final_response
            else:
                return "Audio analysis failed. Please try again."
        else:
            return "Audio analysis service not available."
            
    except Exception as e:
        print(f"❌ Audio-only processing error: {e}")
        return f"Audio processing error: {str(e)}"

@app.route('/text-chat', methods=['POST'])
def text_chat():
    """Text-only chat endpoint"""
    print("💬 Text Chat Flask: Processing request started")
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', '')
        memory_context = data.get('memory_context', '')
        
        print(f"📝 Text Chat Flask: Message - {message}")
        print(f"🆔 Text Chat Flask: Session - {session_id}")
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        # Ensure session is started
        if not current_session["session_id"]:
            current_session["session_id"] = session_id or f"session_{int(time.time())}"
        
        # Process text chat (simplified - no complex RAG)
        response = process_text_chat(message, session_id)
        
        # Add interaction to session
        current_session["interactions"].append({
            "timestamp": time.time(),
            "user_input": message,
            "bot_response": response,
            "processing_time": 0
        })
        
        completion_time = datetime.now().isoformat()
        print("✅ Text Chat Flask: Processing completed successfully")
        return jsonify({
            "response": response,
            "session_id": current_session["session_id"],
            "completion_time": completion_time
        })
        
    except Exception as e:
        print(f"❌ Text Chat Flask: Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/new_session', methods=['POST'])
def new_session():
    """Start a new session"""
    try:
        data = request.get_json()
        user_query = data.get('user_query', '')
        
        # Start new session
        start_new_session()
        
        # Simplified - no complex RAG memory context
        current_session["memory_context"] = ""
        
        return jsonify({
            "status": "success",
            "session_id": current_session["session_id"],
            "memory_context": ""
        })
        
    except Exception as e:
        print(f"❌ Error starting new session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/session_history', methods=['GET'])
def get_session_history():
    """Get session history"""
    try:
        if not rag_system:
            return jsonify({"error": "RAG system not available"}), 500
        
        limit = request.args.get('limit', 10, type=int)
        history = rag_system.get_session_history(limit=limit)
        
        return jsonify({
            "status": "success",
            "history": history
        })
        
    except Exception as e:
        print(f"❌ Error getting session history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/current_session', methods=['GET'])
def get_current_session():
    """Get current session info"""
    try:
        return jsonify({
            "status": "success",
            "session": {
                "session_id": current_session["session_id"],
                "start_time": current_session["start_time"],
                "upload_count": len(current_session["uploads"]),
                "interaction_count": len(current_session["interactions"]),
                "memory_context": current_session["memory_context"]
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting current session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/rag_stats', methods=['GET'])
def get_rag_stats():
    """Get RAG system statistics"""
    try:
        if not rag_system:
            return jsonify({"error": "RAG system not available"}), 500
        
        stats = rag_system.get_stats()
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
        
    except Exception as e:
        print(f"❌ Error getting RAG stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/search_past', methods=['POST'])
def search_past_sessions():
    """Search past sessions using RAG"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        if not rag_system:
            return jsonify({"error": "RAG system not available"}), 500
        
        print(f"🔍 RAG Search: Searching for '{query}'")
        
        # Get relevant sessions
        relevant_sessions = rag_system.retrieve_relevant_sessions(query, top_k=3)
        
        if relevant_sessions:
            # Create a summary of relevant past sessions
            summary_parts = [f"Found {len(relevant_sessions)} relevant past sessions:"]
            
            for i, session in enumerate(relevant_sessions, 1):
                # Handle timestamp conversion
                try:
                    if isinstance(session['timestamp'], str):
                        # Parse ISO format string
                        session_date = datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                    else:
                        # Assume it's a Unix timestamp
                        session_date = datetime.fromtimestamp(session['timestamp']).strftime('%Y-%m-%d %H:%M')
                except:
                    session_date = "Unknown date"
                
                relevance = f"{session['relevance_score']:.2f}"
                summary_parts.append(f"\n{i}. Session from {session_date} (relevance: {relevance}):")
                summary_parts.append(f"   {session['summary'][:300]}...")
            
            summary = "\n".join(summary_parts)
            
            return jsonify({
                "found_sessions": len(relevant_sessions),
                "summary": summary,
                "sessions": relevant_sessions
            })
        else:
            return jsonify({
                "found_sessions": 0,
                "summary": "No relevant past sessions found for your query.",
                "sessions": []
            })
            
    except Exception as e:
        print(f"❌ Error searching past sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    # Test fine-tuned model
    fine_tuned_working = False
    if ollama_integration:
        try:
            test_response = ollama_integration.generate_text("Test", max_tokens=10)
            fine_tuned_working = len(test_response) > 0
        except:
            fine_tuned_working = False
    
    status = {
        "gemma3n_2b_loaded": gemma3n_2b_pipeline is not None,
        "ollama_loaded": ollama_integration is not None,
        "fine_tuned_model": "gemma3n-finetuned",
        "fine_tuned_working": fine_tuned_working,
        "rag_loaded": rag_system is not None,
        "current_session": current_session["session_id"] is not None,
        "pipeline": "gemma3n_2b_optimized_with_finetuned_ollama",
        "features": {
            "audio_transcription": "Gemma 3n 2B",
            "image_analysis": "Gemma 3n 2B", 
            "multimodal_analysis": "Gemma 3n 2B (Optimized)",
            "text_enhancement": "Fine-tuned Ollama",
            "session_memory": "Offline RAG",
            "memory_context": "Active",
            "text_chat": "Fine-tuned Ollama"
        }
    }
    return jsonify(status)

if __name__ == '__main__':
    print("🚀 Gemma 3n 2B Flask server with RAG starting...")
    
    models_loaded = initialize_models()
    
    if models_loaded:
        print("✅ All models loaded successfully")
        print("🎯 Pipeline: Gemma 3n 2B with Offline RAG")
        print("🔧 Features: 2B multimodal + Session memory + RAG context + Text chat")
    else:
        print("❌ Models failed to load")
        exit(1)
    
    print("🚀 2B Flask server with RAG starting on http://localhost:5001")
    app.run(debug=False, host='0.0.0.0', port=5001) 