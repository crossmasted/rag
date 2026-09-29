import ollama
import httpx
from app.core.config import settings


class EmbeddingService:
    """文本向量化服务，按 LLM_PROVIDER 分发：

    - ollama   : 本地 bge-m3（默认，本地开发用）
    - dashscope: 通义千问 text-embedding-v3（云端部署时服务器无模型，必须走 API）
    """

    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.EMBED_MODEL
        self.dimension = None
        self.dashscope_embed_url = (
            "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
        )

    async def get_embedding(self, text: str) -> list[float]:
        """获取单条文本向量"""
        if settings.LLM_PROVIDER == "dashscope":
            return self._get_dashscope_embeddings([text])[0]
        return self._get_ollama_embedding(text)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """批量获取向量（dashscope 一次请求完成，ollama 逐条调用）"""
        if not texts:
            return []
        if settings.LLM_PROVIDER == "dashscope":
            return self._get_dashscope_embeddings(texts)
        return [await self._get_ollama_embedding(text) for text in texts]

    def _get_ollama_embedding(self, text: str) -> list[float]:
        """Ollama bge-m3 向量化。固定 keep_alive=-1 让模型常驻显存（配合 chat 模型的
        keep_alive=-1），避免 4GB 显存下每轮问答反复重载模型导致的 60-100 秒卡顿。
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

    def _get_dashscope_embeddings(self, texts: list[str]) -> list[list[float]]:
        """通义千问 text-embedding-v3 向量化（OpenAI 兼容模式）。

        显式指定 dimensions=1024，与本地 bge-m3 的向量维度保持一致，
        保证同一 Qdrant 集合内的向量维度兼容。
        """
        headers = {
            "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.DASHSCOPE_EMBED_MODEL,
            "input": texts,
            "dimensions": 1024,
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(self.dashscope_embed_url, json=body, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(
                f"DashScope 向量化失败: {resp.status_code} {resp.text[:200]}"
            )
        # 按 index 排序，保证返回顺序与入参一致
        data = sorted(resp.json()["data"], key=lambda item: item["index"])
        embeddings = [item["embedding"] for item in data]
        if self.dimension is None:
            self.dimension = len(embeddings[0])
        return embeddings


embedding_service = EmbeddingService()
