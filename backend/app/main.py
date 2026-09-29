from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import documents, chat
from app.services.vector_store import vector_store
from app.services.embeddings import embedding_service

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
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    """启动时初始化向量库"""
    # 获取 embedding 维度并创建集合
    test_embedding = await embedding_service.get_embedding("test")
    vector_store.create_collection(dimension=len(test_embedding))

@app.get("/")
async def root():
    return {"message": "RAG 知识库系统 API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
