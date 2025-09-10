#!/usr/bin/env python3
"""
Optimized RAG System
High-performance offline RAG with improved error handling
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

from config import Config

# Import local embeddings
from local_embeddings import LocalEmbeddings

class OptimizedRAGSystem:
    """High-performance offline RAG system"""

    def __init__(self):
        self.data_dir = Config.RAG_DATA_DIR
        self.sessions_dir = os.path.join(self.data_dir, "sessions")
        self.embeddings_dir = os.path.join(self.data_dir, "embeddings")
        
        # Create directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.embeddings_dir, exist_ok=True)
        
        # Initialize components
        self.embedding_model = None
        self.faiss_index = None
        self.session_metadata = []
        
        # File paths
        self.faiss_index_file = os.path.join(self.embeddings_dir, "faiss_index.bin")
        self.metadata_file = os.path.join(self.data_dir, "session_metadata.json")
        
        # Load existing data
        self._load_system()
    
    def _load_system(self):
        """Load existing RAG system data"""
        try:
            # Load embedding model
            print("🔧 Loading local sentence transformer model...")
            try:
                self.embedding_model = LocalEmbeddings()
                print("✅ Local sentence transformer model loaded")
            except Exception as e:
                print(f"❌ Could not load local sentence transformer model: {e}")
                raise
            
            # Load FAISS index
            print("📥 Loading existing FAISS index...")
            if os.path.exists(self.faiss_index_file):
                self.faiss_index = faiss.read_index(self.faiss_index_file)
                print("✅ FAISS index loaded")
            else:
                # Create new index
                self.faiss_index = faiss.IndexFlatIP(self.embedding_model.embedding_dim)
                print("✅ New FAISS index created")
            
            # Load session metadata
            print("📥 Loading session metadata...")
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    self.session_metadata = json.load(f)
                print(f"✅ Loaded {len(self.session_metadata)} sessions")
            else:
                self.session_metadata = []
                print("✅ New metadata file created")
            
            print("✅ RAG system initialized")
            
        except Exception as e:
            print(f"❌ Error loading RAG system: {e}")
            raise
    
    def store_session(self, session_data: Dict[str, Any]) -> bool:
        """Store session in RAG system"""
        try:
            session_id = session_data["session_id"]
            
            # Check if session already exists
            existing_index = None
            for i, metadata in enumerate(self.session_metadata):
                if metadata["session_id"] == session_id:
                    existing_index = i
                    break
            
            # Generate summary if not provided
            if "summary" not in session_data:
                session_data["summary"] = self._generate_summary(session_data)
            
            # Generate embedding
            summary_embedding = self.embedding_model.encode(session_data["summary"])
            if summary_embedding is None:
                print(f"❌ Failed to generate embedding for session {session_id}")
                return False
            
            # Ensure embedding is 2D
            if len(summary_embedding.shape) == 1:
                summary_embedding = summary_embedding.reshape(1, -1)
            
            # Create session file path
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            # Store session data
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Update metadata
            metadata_entry = {
                "session_id": session_id,
                "timestamp": session_data.get("end_time", time.time()),
                "file_path": session_file,
                "summary": session_data["summary"],
                "interaction_count": len(session_data.get("interactions", [])),
                "upload_count": len(session_data.get("uploads", [])),
                "topics": session_data.get("topics", [])
            }
            
            if existing_index is not None:
                # Update existing session
                self.session_metadata[existing_index] = metadata_entry
                # Update FAISS index (remove old, add new)
                # For simplicity, we'll just add the new embedding
                # In production, you'd want to properly update the index
                self.faiss_index.add(summary_embedding.astype('float32'))
                print(f"🔄 Session {session_id} updated successfully")
            else:
                # Add new session
                self.faiss_index.add(summary_embedding.astype('float32'))
                self.session_metadata.append(metadata_entry)
                print(f"✅ Session {session_id} stored successfully")
            
            # Save updated data
            self._save_system()
            
            return True
            
        except Exception as e:
            print(f"❌ Error storing session: {e}")
            return False
    
    def retrieve_relevant_sessions(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant sessions based on query"""
        if limit is None:
            limit = Config.RAG_MAX_RETRIEVED_SESSIONS
        
        try:
            if not query.strip():
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            if query_embedding is None:
                return []
            
            # Ensure embedding is 2D
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(query_embedding.astype('float32'), limit)
            
            # Filter by similarity threshold
            relevant_sessions = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.session_metadata) and score >= Config.RAG_SIMILARITY_THRESHOLD:
                    session_info = self.session_metadata[idx]
                    session_info["similarity_score"] = float(score)
                    relevant_sessions.append(session_info)
            
            return relevant_sessions
            
        except Exception as e:
            print(f"❌ Error retrieving sessions: {e}")
            return []
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sessions with improved timestamp handling"""
        try:
            def convert_timestamp(ts):
                """Convert various timestamp formats to float"""
                if isinstance(ts, (int, float)):
                    return float(ts)
                elif isinstance(ts, str):
                    try:
                        # Try to convert string timestamp to float
                        return float(ts)
                    except ValueError:
                        # Handle ISO datetime strings
                        try:
                            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                            return dt.timestamp()
                        except:
                            return 0.0
                return 0.0
            
            # Sort by timestamp (newest first)
            sorted_sessions = sorted(
                self.session_metadata,
                key=lambda x: convert_timestamp(x['timestamp']),
                reverse=True
            )[:limit]
            
            # Load session data
            history = []
            for session_info in sorted_sessions:
                try:
                    if os.path.exists(session_info['file_path']):
                        with open(session_info['file_path'], 'r') as f:
                            session_data = json.load(f)
                        
                        # Handle both old and new session formats
                        summary = session_info.get("summary") or session_data.get("summary", "No summary available")
                        interaction_count = session_info.get("interaction_count", len(session_data.get("interactions", [])))
                        upload_count = session_info.get("upload_count", len(session_data.get("uploads", [])))
                        topics = session_info.get("topics", session_data.get("topics", []))
                        
                        history.append({
                            "session_id": session_info["session_id"],
                            "timestamp": session_info["timestamp"],
                            "summary": summary,
                            "interaction_count": interaction_count,
                            "upload_count": upload_count,
                            "topics": topics
                        })
                except Exception as e:
                    print(f"⚠️ Error loading session {session_info.get('session_id', 'unknown')}: {e}")
                    continue
            
            return history
            
        except Exception as e:
            print(f"❌ Error getting recent sessions: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        try:
            total_sessions = len(self.session_metadata)
            faiss_index_size = self.faiss_index.ntotal if self.faiss_index else 0
            
            # Count different types
            total_interactions = sum(s.get("interaction_count", 0) for s in self.session_metadata)
            total_uploads = sum(s.get("upload_count", 0) for s in self.session_metadata)
            
            # Count upload types
            image_uploads = 0
            audio_uploads = 0
            text_interactions = 0
            
            for session_info in self.session_metadata:
                try:
                    if os.path.exists(session_info['file_path']):
                        with open(session_info['file_path'], 'r') as f:
                            session_data = json.load(f)
                        
                        uploads = session_data.get("uploads", [])
                        for upload in uploads:
                            if upload.get("type") == "image":
                                image_uploads += 1
                            elif upload.get("type") == "audio":
                                audio_uploads += 1
                        
                        interactions = session_data.get("interactions", [])
                        text_interactions += sum(1 for i in interactions if i.get("type") == "text")
                        
                except Exception:
                    continue
            
            return {
                "total_sessions": total_sessions,
                "faiss_index_size": faiss_index_size,
                "total_interactions": total_interactions,
                "total_uploads": total_uploads,
                "image_uploads": image_uploads,
                "audio_uploads": audio_uploads,
                "text_interactions": text_interactions
            }
            
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Alias for get_statistics for backward compatibility"""
        return self.get_statistics()
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Alias for get_recent_sessions for backward compatibility"""
        return self.get_recent_sessions(limit)
    
    def create_memory_context(self, query: str) -> str:
        """Create memory context for new sessions"""
        try:
            relevant_sessions = self.retrieve_relevant_sessions(query, limit=2)
            
            if not relevant_sessions:
                print("🔍 No relevant sessions found for memory context")
                return ""
            
            # Create simple context with session summaries
            context_parts = ["Based on your previous learning sessions:"]
            
            for i, session in enumerate(relevant_sessions, 1):
                # Format the date properly
                try:
                    if isinstance(session['timestamp'], str):
                        session_date = datetime.fromisoformat(session['timestamp'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                    else:
                        session_date = datetime.fromtimestamp(session['timestamp']).strftime('%Y-%m-%d %H:%M')
                except:
                    session_date = "Unknown date"
                
                summary = session.get('summary', 'No summary available')
                # Replace any [Date of Session] placeholders with actual date
                summary = summary.replace("[Date of Session]", session_date)
                summary = summary.replace("[Date of session]", session_date)
                
                # Just use the first 400 chars of the summary
                context_parts.append(f"\n{i}. Session from {session_date}:")
                context_parts.append(f"   {summary[:400]}...")
            
            context_parts.append("\nI'll build on this knowledge in our current session.")
            
            context = "\n".join(context_parts)
            print(f"🧠 Created memory context: {len(context)} chars")
            return context
            
        except Exception as e:
            print(f"❌ Error creating memory context: {e}")
            return ""
    
    def _generate_summary(self, session_data: Dict[str, Any]) -> str:
        """Generate session summary"""
        interactions = session_data.get("interactions", [])
        uploads = session_data.get("uploads", [])
        
        if not interactions:
            return "Empty session"
        
        # Count different types
        text_count = sum(1 for i in interactions if i.get("type") == "text")
        image_count = sum(1 for u in uploads if u.get("type") == "image")
        audio_count = sum(1 for u in uploads if u.get("type") == "audio")
        
        # Get recent interactions
        recent_interactions = interactions[-3:]  # Last 3
        recent_summary = []
        for interaction in recent_interactions:
            content = interaction.get("content", "")
            recent_summary.append(f"  * {content[:50]}...")
        
        summary = f"""Session Summary:
- Total interactions: {len(interactions)}
- Images processed: {image_count}
- Audio files processed: {audio_count}
- Text interactions: {text_count}
- Recent interactions:
{chr(10).join(recent_summary)}"""
        
        return summary
    
    def _save_system(self):
        """Save FAISS index and metadata"""
        try:
            # Save FAISS index
            faiss.write_index(self.faiss_index, self.faiss_index_file)
            
            # Save metadata
            with open(self.metadata_file, 'w') as f:
                json.dump(self.session_metadata, f, indent=2)
            
            print("💾 RAG system data saved")
            
        except Exception as e:
            print(f"❌ Error saving RAG system: {e}")


# Global RAG system instance
_rag_system = None

def get_rag_system() -> OptimizedRAGSystem:
    """Get global RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = OptimizedRAGSystem()
    return _rag_system

def initialize_rag() -> bool:
    """Initialize RAG system"""
    try:
        get_rag_system()
        return True
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        return False
