import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    MAX_CONCURRENT: int = int(os.getenv("MAX_CONCURRENT", "5"))
    COLLECTION_NAME: str = "rag_documents"

settings = Settings()
