import ollama
from app.core.config import settings

class EmbeddingService:
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = "bge-m3"
        self.dimension = None
    
    async def get_embedding(self, text: str) -> list[float]:
        """获取文本向量
        
        固定 keep_alive=-1 让 bge-m3 常驻显存（配合 chat 模型的 keep_alive=-1），
        避免 4GB 显存下每轮问答反复重载模型导致的 60-100 秒卡顿。
        同时缩小 num_ctx（单条嵌入用不到大上下文），降低显存占用。
        """
        response = self.client.embeddings(
            model=self.model,
            prompt=text,
            keep_alive=-1,
            options={"num_ctx": 512},
        )
        embedding = response["embedding"]
        if self.dimension is None:
            self.dimension = len(embedding)
        return embedding
    
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """批量获取向量"""
        embeddings = []
        for text in texts:
            emb = await self.get_embedding(text)
            embeddings.append(emb)
        return embeddings

embedding_service = EmbeddingService()
