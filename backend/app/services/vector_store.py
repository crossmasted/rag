from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, PointIdsList, Filter, FieldCondition, MatchValue
from app.core.config import settings
import uuid

class VectorStoreService:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.COLLECTION_NAME
    
    def create_collection(self, dimension: int = 1024):
        """创建向量集合"""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )
    
    def add_documents(self, texts: list[str], embeddings: list[list[float]], 
                     metadatas: list[dict], access_level: str = "public"):
        """添加文档到向量库"""
        points = []
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": text,
                    "access_level": access_level,
                    **metadata
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    def search(self, query_embedding: list[float], access_level: str = "public", 
               limit: int = 5) -> list[dict]:
        """搜索相似文档"""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="access_level",
                        match=MatchValue(value=access_level)
                    )
                ]
            ),
            limit=limit
        )
        
        return [
            {
                "text": hit.payload["text"],
                "score": hit.score,
                "metadata": {k: v for k, v in hit.payload.items() if k not in ["text", "access_level"]}
            }
            for hit in results
        ]
    
    def list_documents(self) -> list[dict]:
        """列出所有已入库文档（按 doc_id 聚合）"""
        docs_map = {}
        offset = None
        while True:
            records, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for record in records:
                payload = record.payload or {}
                doc_id = payload.get("doc_id")
                if doc_id is None:
                    continue
                if doc_id not in docs_map:
                    docs_map[doc_id] = {
                        "doc_id": doc_id,
                        "filename": payload.get("filename") or doc_id,
                        "chunks": 0,
                    }
                docs_map[doc_id]["chunks"] += 1
            if next_offset is None:
                break
            offset = next_offset
        return sorted(docs_map.values(), key=lambda d: d["filename"])

    def document_exists(self, doc_id: str) -> bool:
        """判断同名文档是否已入库"""
        result = self.client.count(
            collection_name=self.collection_name,
            count_filter=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
            ),
            exact=True,
        )
        return result.count > 0

    def deduplicate_documents(self) -> int:
        """清理重复片段：同一 (doc_id, chunk_index) 只保留一个，返回删除数量"""
        seen = {}
        duplicate_ids = []
        offset = None
        while True:
            records, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for record in records:
                payload = record.payload or {}
                key = (payload.get("doc_id"), payload.get("chunk_index"))
                if key in seen:
                    duplicate_ids.append(record.id)
                else:
                    seen[key] = record.id
            if next_offset is None:
                break
            offset = next_offset
        if duplicate_ids:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=duplicate_ids),
            )
        return len(duplicate_ids)

    def delete_document(self, doc_id: str):
        """删除文档"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
        )

vector_store = VectorStoreService()
