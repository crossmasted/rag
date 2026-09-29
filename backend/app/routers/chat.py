from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.core.config import settings
import ollama
import json
import asyncio
import time

router = APIRouter()

# 并发控制信号量
semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT)

@router.get("/stream")
async def chat_stream(query: str, access_level: str = "public"):
    """流式问答"""
    return StreamingResponse(
        event_stream(query, access_level),
        media_type="text/event-stream",
    )


async def event_stream(query: str, access_level: str):
    # 检查是否需要排队
    if semaphore.locked():
        queue_count = settings.MAX_CONCURRENT - semaphore._value
        yield f"data: {json.dumps({'type': 'queue', 'message': f'当前排队人数: {queue_count}, 请稍候...'})}\n\n"
    
    async with semaphore:
        try:
            t0 = time.monotonic()
            # 1. 获取查询向量
            query_embedding = await embedding_service.get_embedding(query)
            t1 = time.monotonic()
            print(f"[timing] embed={t1 - t0:.2f}s", flush=True)
            
            # 2. 检索相关文档
            results = vector_store.search(query_embedding, access_level, limit=5)
            t2 = time.monotonic()
            print(f"[timing] search={t2 - t1:.2f}s results={len(results)}", flush=True)
            
            # 3. 构建上下文
            context = "\n\n".join([f"参考资料{i+1}:\n{r['text']}" for i, r in enumerate(results)])
            
            # 4. 构建 Prompt
            prompt = f"""基于以下参考资料回答用户问题。如果参考资料中没有相关信息，请说"根据现有资料无法回答该问题"。

{context}

用户问题: {query}

回答:"""
            
            # 5. 调用 LLM 生成回答
            client = ollama.Client(host=settings.OLLAMA_HOST)
            t3 = time.monotonic()
            
            # 发送检索到的参考信息
            sources = [
                {
                    "metadata": r["metadata"],
                    "text": r["text"],
                    "score": r["score"],
                }
                for r in results
            ]
            yield f"data: {json.dumps({'type': 'sources', 'count': len(results), 'sources': sources})}\n\n"
            
            # 流式生成（限制最大输出长度，避免回答过长拖慢响应）
            # keep_alive=-1 让 qwen2.5:3b 常驻显存，避免每轮问答反复重载
            stream = client.chat(
                model='qwen2.5:3b',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True,
                keep_alive=-1,
                options={
                    'num_predict': 512,
                    'temperature': 0.4,
                }
            )
            
            for chunk in stream:
                content = chunk['message']['content']
                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            
            t4 = time.monotonic()
            print(f"[timing] gen={t4 - t3:.2f}s total={t4 - t0:.2f}s", flush=True)
            
            # 发送完成标记
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
