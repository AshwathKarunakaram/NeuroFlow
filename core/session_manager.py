#!/usr/bin/env python3
"""
Optimized Session Manager
Handles session state and persistence
"""

import os
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import Config

class SessionManager:
    """Centralized session management"""
    
    def __init__(self):
        self.current_session = {
            "session_id": None,
            "start_time": None,
            "uploads": [],
            "interactions": [],
            "topics": [],
            "memory_context": ""
        }
        self._session_cache = {}
    
    def start_new_session(self) -> str:
        """Start a new session"""
        # Store previous session if exists
        if self.current_session["session_id"] and len(self.current_session["interactions"]) > 0:
            self._store_current_session()
        
        # Initialize new session
        session_id = str(uuid.uuid4())
        self.current_session.update({
            "session_id": session_id,
            "start_time": time.time(),
            "uploads": [],
            "interactions": [],
            "topics": [],
            "memory_context": ""
        })
        
        print(f"🆕 New session started: {session_id}")
        return session_id
    
    def add_interaction(self, interaction_type: str, content: str, response: str, 
                       uploads: Optional[List[Dict]] = None) -> None:
        """Add interaction to current session"""
        interaction = {
            "id": str(uuid.uuid4()),
            "type": interaction_type,
            "content": content,
            "response": response,
            "timestamp": time.time()
        }
        
        self.current_session["interactions"].append(interaction)
        
        # Add uploads if provided
        if uploads:
            self.current_session["uploads"].extend(uploads)
        
        # Update memory context with recent interactions
        self._update_memory_context()
        
        print(f"📝 Added {interaction_type} interaction to session")
    
    def get_current_session(self) -> Dict[str, Any]:
        """Get current session info"""
        return {
            "session_id": self.current_session["session_id"],
            "start_time": self.current_session["start_time"],
            "interaction_count": len(self.current_session["interactions"]),
            "upload_count": len(self.current_session["uploads"]),
            "memory_context": self.current_session["memory_context"]
        }
    
    def get_session_summary(self) -> str:
        """Generate session summary for RAG storage"""
        if not self.current_session["interactions"]:
            return "Empty session"
        
        interactions = self.current_session["interactions"]
        uploads = self.current_session["uploads"]
        
        # Count different types
        text_count = sum(1 for i in interactions if i["type"] == "text")
        image_count = sum(1 for u in uploads if u.get("type") == "image")
        audio_count = sum(1 for u in uploads if u.get("type") == "audio")
        
        # Get recent interactions
        recent_interactions = interactions[-3:]  # Last 3
        recent_summary = []
        for interaction in recent_interactions:
            recent_summary.append(f"  * {interaction['content'][:50]}...")
        
        summary = f"""Session Summary:
- Total interactions: {len(interactions)}
- Images processed: {image_count}
- Audio files processed: {audio_count}
- Text interactions: {text_count}
- Recent interactions:
{chr(10).join(recent_summary)}"""
        
        return summary
    
    def _update_memory_context(self) -> None:
        """Update memory context with recent interactions"""
        recent_interactions = self.current_session["interactions"][-5:]  # Last 5
        context_parts = []
        
        for interaction in recent_interactions:
            context_parts.append(f"User: {interaction['content']}")
            context_parts.append(f"AI: {interaction['response']}")
        
        self.current_session["memory_context"] = "\n".join(context_parts)
    
    def _store_current_session(self) -> None:
        """Store current session in RAG system"""
        session_data = {
            "session_id": self.current_session["session_id"],
            "start_time": self.current_session["start_time"],
            "end_time": time.time(),
            "interactions": self.current_session["interactions"],
            "uploads": self.current_session["uploads"],
            "topics": self.current_session["topics"],
            "memory_context": self.current_session["memory_context"],
            "summary": self.get_session_summary()
        }
        
        # Store in RAG system
        try:
            from core.rag_system import get_rag_system
            rag_system = get_rag_system()
            if rag_system.store_session(session_data):
                print(f"💾 Session {self.current_session['session_id']} stored in RAG system")
            else:
                print(f"❌ Failed to store session {self.current_session['session_id']} in RAG system")
        except Exception as e:
            print(f"❌ Error storing session in RAG system: {e}")
            # Fallback to cache
            self._session_cache[self.current_session["session_id"]] = session_data
            print(f"💾 Session {self.current_session['session_id']} stored in cache as fallback")
    
    def get_cached_sessions(self) -> List[Dict[str, Any]]:
        """Get cached sessions"""
        return list(self._session_cache.values())
    
    def store_current_session(self) -> bool:
        """Force store current session in RAG system"""
        if self.current_session["session_id"] and len(self.current_session["interactions"]) > 0:
            self._store_current_session()
            return True
        return False
    
    def clear_current_session(self) -> None:
        """Clear current session"""
        # Store current session before clearing
        if self.current_session["session_id"] and len(self.current_session["interactions"]) > 0:
            self._store_current_session()
        
        self.current_session.update({
            "session_id": None,
            "start_time": None,
            "uploads": [],
            "interactions": [],
            "topics": [],
            "memory_context": ""
        })
        print("🗑️ Current session cleared")
