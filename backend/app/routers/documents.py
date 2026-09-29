from fastapi import APIRouter, UploadFile, File, Form
from app.services.document import document_service
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
import os
import tempfile

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    access_level: str = Form("public")
):
    """上传文档"""
    doc_id = os.path.splitext(file.filename)[0]
    # 同名文档去重：已入库则跳过，避免重复向量
    if vector_store.document_exists(doc_id):
        return {
            "message": "文档已存在，跳过重复上传",
            "filename": file.filename,
            "skipped": True,
        }

    # 保存临时文件
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 解析文档
        if suffix.lower() == '.md':
            text = content.decode('utf-8')
            chunks = document_service.parse_markdown(text)
        elif suffix.lower() == '.pdf':
            chunks = document_service.parse_pdf(tmp_path)
        else:
            return {"error": "不支持的文件格式，仅支持 .md 和 .pdf"}
        
        # 生成向量
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await embedding_service.get_embeddings(texts)
        
        # 准备元数据
        metadatas = []
        doc_id = os.path.splitext(file.filename)[0]
        for i, chunk in enumerate(chunks):
            metadata = chunk["metadata"].copy()
            metadata["doc_id"] = doc_id
            metadata["chunk_index"] = i
            metadata["filename"] = file.filename
            metadatas.append(metadata)
        
        # 存入向量库
        vector_store.add_documents(texts, embeddings, metadatas, access_level)
        
        return {
            "message": "上传成功",
            "filename": file.filename,
            "chunks_count": len(chunks)
        }
    
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/list")
async def list_documents():
    """列出所有已入库文档（按 doc_id 聚合）"""
    documents = vector_store.list_documents()
    return {"documents": documents, "total": len(documents)}

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    vector_store.delete_document(doc_id)
    return {"message": "删除成功"}
