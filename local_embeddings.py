#!/usr/bin/env python3
"""
Local sentence transformer embeddings for offline RAG system
Downloads once, works offline forever
"""

import os
import numpy as np
from typing import List, Union
import hashlib

class LocalEmbeddings:
    """Local sentence transformer embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_dim = 384
        self.cache = {}
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            # Set environment variables for offline mode
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # Try to load from cache first
            cache_dir = os.path.expanduser(f"~/.cache/torch/sentence_transformers/{self.model_name}")
            
            if os.path.exists(cache_dir):
                print(f"📁 Loading sentence transformer from cache: {cache_dir}")
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(cache_dir)
                print("✅ Sentence transformer loaded from cache")
            else:
                print(f"⚠️ No cached model found. Downloading {self.model_name}...")
                print("💡 This will only happen once - the model will be cached for offline use")
                
                # Temporarily enable online mode for download
                os.environ['HF_HUB_OFFLINE'] = '0'
                os.environ['TRANSFORMERS_OFFLINE'] = '0'
                
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                
                # Switch back to offline mode
                os.environ['HF_HUB_OFFLINE'] = '1'
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                
                print("✅ Sentence transformer downloaded and cached")
                
        except Exception as e:
            print(f"❌ Error loading sentence transformer: {e}")
            print("🔄 Falling back to hash-based embeddings")
            self.model = None
    
    def _generate_hash_embedding(self, text: str) -> List[float]:
        """Generate deterministic embedding based on text hash"""
        # Create hash of text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to numbers
        embedding = []
        for i in range(0, len(text_hash), 2):
            if len(embedding) >= self.embedding_dim:
                break
            # Convert hex to float between -1 and 1
            hex_val = text_hash[i:i+2]
            num = (int(hex_val, 16) - 128) / 128.0
            embedding.append(num)
        
        # Pad or truncate to exact dimension
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        
        return embedding[:self.embedding_dim]
    
    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) to embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        
        for text in texts:
            # Check cache first
            if text in self.cache:
                embeddings.append(self.cache[text])
                continue
            
            # Generate embedding
            if self.model:
                try:
                    embedding = self.model.encode([text])[0].tolist()
                except Exception as e:
                    print(f"⚠️ Sentence transformer failed, using hash fallback: {e}")
                    embedding = self._generate_hash_embedding(text)
            else:
                embedding = self._generate_hash_embedding(text)
            
            self.cache[text] = embedding
            embeddings.append(embedding)
        
        return np.array(embeddings, dtype=np.float32)
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text to embedding"""
        return self.encode([text])[0]

def test_local_embeddings():
    """Test the local embeddings"""
    print("🧪 Testing local embeddings...")
    
    try:
        embeddings = LocalEmbeddings()
        
        # Test single text
        text = "This is a test sentence for embedding generation."
        embedding = embeddings.encode_single(text)
        print(f"✅ Single embedding shape: {embedding.shape}")
        print(f"✅ Embedding values: {embedding[:5]}...")
        
        # Test multiple texts
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        embeddings_array = embeddings.encode(texts)
        print(f"✅ Multiple embeddings shape: {embeddings_array.shape}")
        
        print("✅ Local embeddings test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Local embeddings test failed: {e}")
        return False

if __name__ == "__main__":
    test_local_embeddings() 