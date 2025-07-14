# backend/app/chroma_handler.py
import chromadb
from chromadb.config import Settings
from typing import Dict, List, Optional
import threading
from pathlib import Path
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
            with self._lock:
                self.debate_collection.add(
                    documents=[round_data["content"]],
                    metadatas=[metadata],
                    ids=f"round_{round_data['round_number']}"
                )
            return True
        except Exception as e:
            logger.error(f"Failed to log round {round_data.get('round_number')}: {str(e)}")
            return False

    def get_transcript(self, num_rounds: int = 5) -> List[Dict]:
        try:
            results = self.debate_collection.get(
                limit=num_rounds,
                include=["metadatas", "documents"]
            )
            return [
                {"content": doc, "meta": meta}
                for doc, meta in zip(results["documents"], results["metadatas"])
            ]
        except Exception as e:
            logger.error(f"Transcript retrieval failed: {str(e)}")
            return []
