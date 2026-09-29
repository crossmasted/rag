# RAG 系统架构设计文档

## 系统概述

本系统是一个基于检索增强生成（RAG）技术的智能知识库问答系统，支持多格式文档上传、语义检索、流式问答等功能。

## 核心架构

### 1. 整体架构图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Vue 3     │────▶│   FastAPI   │────▶│   Ollama    │
│  前端界面    │◀────│   后端服务   │◀────│  LLM 服务   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Qdrant    │
                    │  向量数据库  │
                    └─────────────┘
```

### 2. 核心流程

**文档入库流程：**
1. 用户上传 Markdown/PDF 文档
2. 后端解析文档，按语义分块（500-800 tokens）
3. 使用 BGE-M3 模型生成向量
4. 向量 + 元数据存入 Qdrant

**问答流程：**
1. 用户输入问题
2. 问题向量化
3. Qdrant 检索 Top-K 相似文档
4. 构建 Prompt（包含检索结果）
5. LLM 生成回答
6. SSE 流式返回前端

## 技术选型说明

### 为什么用 FastAPI？
- 异步支持好，适合 SSE 流式响应
- 自动生成 API 文档
- 与 Python AI 生态无缝集成

### 为什么用 Qdrant？
- 专为向量检索优化
- 支持 payload 过滤（实现权限隔离）
- 本地部署，性能优秀

### 为什么用 Ollama？
- 本地运行，零 API 成本
- 支持多种开源模型
- 统一的 API 接口

## 关键技术实现

### 1. 并发控制

使用 `asyncio.Semaphore` 实现：
```python
semaphore = asyncio.Semaphore(5)  # 最多5人同时

async def chat():
    await semaphore.acquire()  # 获取许可
    try:
        # 处理请求
        pass
    finally:
        semaphore.release()  # 释放许可
```

### 2. 权限隔离

通过 Qdrant 的 payload filter 实现：
```python
# 查询时强制过滤
results = client.search(
    collection_name="docs",
    query_vector=embedding,
    query_filter=Filter(
        must=[FieldCondition(key="access_level", match="public")]
    )
)
```

### 3. 流式响应

使用 SSE（Server-Sent Events）：
```python
async def stream():
    for chunk in llm.stream():
        yield f"data: {json.dumps(chunk)}\n\n"
```

### 4. 文档分块策略

- **Markdown**: 按标题层级切分，保留结构
- **PDF**: 按页提取，按段落合并到 500-800 tokens
- **重叠**: 相邻 chunk 保留 50-100 tokens 重叠，防止语义断裂

## 性能优化

1. **向量维度**: BGE-M3 使用 1024 维，平衡精度与速度
2. **检索数量**: Top-5 检索，兼顾相关性与上下文长度
3. **流式输出**: 减少首字延迟，提升用户体验
4. **并发限流**: 防止资源耗尽，保证服务稳定

## 扩展方向

1. **混合检索**: 结合 BM25 + 向量检索
2. **Rerank**: 使用 bge-reranker 对结果重排序
3. **父子分块**: 小块匹配，大块上下文
4. **多轮对话**: 引入对话历史管理
5. **增量索引**: 文档更新时只重建相关向量
