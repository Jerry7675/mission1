# backend/app/chroma_handler.py
import chromadb
from chromadb.config import Settings
from typing import Dict, List, Optional
import threading
from pathlib import Path
import uuid
from datetime import datetime
from . import logger, CHROMA_DIR

class ChromaHandler:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            self.client = chromadb.PersistentClient(
                path=str(CHROMA_DIR),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            self.debate_collection = self.client.get_or_create_collection(
                name="debate_transcripts"
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"ChromaDB init failed: {str(e)}")
            raise

    def log_debate_round(self, round_data: Dict, metadata: Optional[Dict] = None) -> bool:
        try:
            if not metadata or not isinstance(metadata, dict) or len(metadata) == 0:
                raise ValueError("Expected metadata to be a non-empty dict")
            
            # Create unique ID 
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = f"{timestamp}_topic_{hash(metadata.get('topic', ''))}_round_{round_data['round_number']}"
            
         
            enhanced_metadata = {
                **metadata,
                "timestamp": datetime.now().isoformat(),
                "debate_session_id": f"{timestamp}_{hash(metadata.get('topic', ''))}"
            }
            
            with self._lock:
                self.debate_collection.add(
                    documents=[round_data["content"]],
                    metadatas=[enhanced_metadata],
                    ids=[unique_id]  # Use unique ID instead of generic round number
                )
            logger.info(f"Successfully logged round {round_data['round_number']} with ID: {unique_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to log round {round_data.get('round_number')}: {str(e)}")
            return False

    def get_transcript(self, num_rounds: int = 5) -> List[Dict]:
        try:
            # Query with ordering recent first
            results = self.debate_collection.get(
                limit=num_rounds * 3,  
                include=["metadatas", "documents"]
            )
            
            # Sort by timestamp  recent first
            combined_results = [
                {"content": doc, "metadata": meta}
                for doc, meta in zip(results["documents"], results["metadatas"])
            ]
            
            
            combined_results.sort(
                key=lambda x: x["metadata"].get("timestamp", ""), 
                reverse=True
            )
            
            return combined_results[:num_rounds]
        except Exception as e:
            logger.error(f"Transcript retrieval failed: {str(e)}")
            return []

    def get_debate_sessions(self, limit: int = 10) -> List[Dict]:
        """Get complete debate sessions grouped by session ID"""
        try:
            results = self.debate_collection.get(
                limit=limit * 5,  
                include=["metadatas", "documents"]
            )
            
            # Group by debate session ID
            sessions = {}
            for doc, meta in zip(results["documents"], results["metadatas"]):
                session_id = meta.get("debate_session_id", "unknown")
                if session_id not in sessions:
                    sessions[session_id] = {
                        "topic": meta.get("topic", "Unknown"),
                        "timestamp": meta.get("timestamp", ""),
                        "rounds": []
                    }
                sessions[session_id]["rounds"].append({
                    "content": doc,
                    "metadata": meta
                })
            
            # Sort sessions by timestamp and limit results
            session_list = list(sessions.values())
            session_list.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return session_list[:limit]
        except Exception as e:
            logger.error(f"Session retrieval failed: {str(e)}")
            return []