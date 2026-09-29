import os
from pathlib import Path
from dotenv import load_dotenv

# .env 位于项目根目录（backend/app/core/config.py 上溯三级）
_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_ROOT / ".env")
load_dotenv()

class Settings:
    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "qwen2.5:3b")
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "bge-m3")

    # 生成提供商: ollama（本地）或 dashscope（云端 API）
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    # DashScope（通义千问）API Key，仅 LLM_PROVIDER=dashscope 时使用
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_MODEL: str = os.getenv("DASHSCOPE_MODEL", "qwen-plus")

    # Qdrant
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    MAX_CONCURRENT: int = int(os.getenv("MAX_CONCURRENT", "5"))
    COLLECTION_NAME: str = "rag_documents"

    # MySQL
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "rag")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "rag_kb")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy MySQL 连接串"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

settings = Settings()
