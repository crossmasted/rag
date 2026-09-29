from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
import ollama
import json
import asyncio
import time
import httpx

router = APIRouter()

# 并发控制信号量
semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT)


@router.get("/stream")
async def chat_stream(
    query: str,
    user: User = Depends(get_current_user),
):
    """流式问答（需登录）"""
    return StreamingResponse(
        event_stream(query, user),
        media_type="text/event-stream",
    )


def stream_dashscope(prompt: str):
    """通过 DashScope（通义千问）流式生成回答"""
    import httpx as _httpx

    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.DASHSCOPE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "temperature": 0.4,
        "max_tokens": 512,
    }
    with _httpx.Client(timeout=120) as client:
        with client.stream("POST", url, json=body, headers=headers) as resp:
            if resp.status_code != 200:
                yield f"data: {json.dumps({'type': 'error', 'message': f'DashScope 调用失败: {resp.status_code} {resp.text[:200]}'})}\n\n"
                return
            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"
                except Exception:
                    continue


async def event_stream(query: str, user: User):
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

            # 2. 按用户访问级别检索
            results = vector_store.search(query_embedding, user.access_level, limit=5)
            t2 = time.monotonic()
            print(f"[timing] search={t2 - t1:.2f}s results={len(results)}", flush=True)

            # 3. 构建上下文
            context = "\n\n".join([f"参考资料{i+1}:\n{r['text']}" for i, r in enumerate(results)])

            # 4. 构建 Prompt
            prompt = f"""基于以下参考资料回答用户问题。如果参考资料中没有相关信息，请说"根据现有资料无法回答该问题"。

{context}

用户问题: {query}

回答:"""

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

            # 5. 调用 LLM 生成回答（按提供商分发）
            t3 = time.monotonic()
            if settings.LLM_PROVIDER == "dashscope":
                gen_stream = stream_dashscope(prompt)
            else:
                client = ollama.Client(host=settings.OLLAMA_HOST)
                gen_stream = client.chat(
                    model=settings.CHAT_MODEL,
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True,
                    keep_alive=-1,
                    options={
                        'num_predict': 512,
                        'temperature': 0.4,
                    }
                )
                gen_stream = iter(chunk['message']['content'] for chunk in gen_stream)

            for content in gen_stream:
                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

            t4 = time.monotonic()
            print(f"[timing] gen={t4 - t3:.2f}s total={t4 - t0:.2f}s", flush=True)

            # 发送完成标记
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
