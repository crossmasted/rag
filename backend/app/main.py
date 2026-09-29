from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import documents, chat, auth
from app.services.vector_store import vector_store
from app.services.embeddings import embedding_service
from app.core.db import Base, engine
from app import models  # noqa: F401  确保模型已注册
from app.core.config import settings

app = FastAPI(title="RAG 知识库系统")

# CORS
# 注意：allow_origins=["*"] 仅适用于本地开发。若要部署到公网，
# 请收敛为具体域名，并注意 allow_credentials=True 与 "*" 的浏览器安全限制。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.on_event("startup")
async def startup_event():
    """启动时初始化数据库表与向量库"""
    # 建表（若 MySQL 未连上会在此报错，便于快速发现）
    Base.metadata.create_all(bind=engine)
    # 获取 embedding 维度并创建集合
    # dashscope 模式下未配置 API Key 时跳过向量库初始化，避免启动即崩；
    # 补齐 Key 后重启服务即可正常初始化。
    if settings.LLM_PROVIDER == "dashscope" and not settings.DASHSCOPE_API_KEY:
        print("SKIP: LLM_PROVIDER=dashscope but DASHSCOPE_API_KEY is empty, skip vector store init")
        return
    test_embedding = await embedding_service.get_embedding("test")
    vector_store.create_collection(dimension=len(test_embedding))

@app.get("/")
async def root():
    return {"message": "RAG 知识库系统 API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
