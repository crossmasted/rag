<template>
  <div class="chat-container">
    <el-card class="chat-card">
      <template #header>
        <div class="card-header">
          <h2>RAG 知识库问答</h2>
          <el-upload
            class="upload-btn"
            :show-file-list="false"
            :before-upload="handleUpload"
            accept=".md,.pdf"
          >
            <el-button type="primary" :icon="Upload">上传文档</el-button>
          </el-upload>
        </div>
      </template>

      <div v-if="documents.length > 0" class="doc-list">
        <span class="doc-list-title">知识库已有文档：</span>
        <el-tag
          v-for="doc in documents"
          :key="doc.doc_id"
          size="small"
          type="info"
          class="doc-tag"
        >
          {{ doc.filename }}（{{ doc.chunks }} 片段）
        </el-tag>
      </div>
      <div v-else class="doc-list doc-list-empty">知识库暂无文档，请先上传</div>

      <div class="messages" ref="messagesRef">
        <div v-for="(msg, index) in messages" :key="index" class="message">
          <div v-if="msg.role === 'user'" class="user-message">
            <div class="content">{{ msg.content }}</div>
          </div>
          <div v-else class="assistant-message">
            <div class="content">
              <div v-if="msg.sources && msg.sources.length > 0" class="sources">
                <el-tag size="small" type="info">参考了 {{ msg.sources.length }} 个片段</el-tag>
                <div
                  v-for="(src, i) in msg.sources"
                  :key="i"
                  class="source-item"
                >
                  <div class="source-head" @click="src.expanded = !src.expanded">
                    <span class="source-name">{{ src.metadata.filename }}</span>
                    <span v-if="src.metadata.page" class="source-meta">第 {{ src.metadata.page }} 页</span>
                    <span v-if="src.metadata.title" class="source-meta">· {{ src.metadata.title }}</span>
                    <span class="source-score">{{ Math.round((src.score || 0) * 100) }}%</span>
                    <span class="source-toggle">{{ src.expanded ? '收起' : '展开' }}</span>
                  </div>
                  <div v-if="src.expanded" class="source-text">{{ src.text }}</div>
                </div>
              </div>
              <div class="text" v-html="renderMarkdown(msg.content)"></div>
              <div v-if="msg.queue" class="queue-info">
                <el-icon class="is-loading"><Loading /></el-icon>
                {{ msg.queue }}
              </div>
            </div>
          </div>
        </div>
        <div v-if="loading" class="assistant-message">
          <div class="content">
            <el-icon class="is-loading"><Loading /></el-icon>
            正在思考...
          </div>
        </div>
      </div>

      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="输入问题，Ctrl+Enter 发送"
          @keydown.ctrl.enter="sendMessage"
        />
        <el-button
          type="primary"
          :loading="loading"
          @click="sendMessage"
          :disabled="!inputText.trim()"
        >
          发送
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { Upload, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { uploadDocument, getChatStream, listDocuments } from '../api'

// 单换行也转 <br>（breaks），这样“第一点/第二点/第三点”能逐行展示
marked.use({ breaks: true, gfm: true })

const renderMarkdown = (text) => DOMPurify.sanitize(marked.parse(text || ''))

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref(null)
const documents = ref([])

const loadDocuments = async () => {
  try {
    const res = await listDocuments()
    documents.value = res.data.documents
  } catch (err) {
    console.error('加载文档列表失败：' + err.message)
  }
}

onMounted(loadDocuments)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const handleUpload = async (file) => {
  try {
    const res = await uploadDocument(file)
    if (res.data.skipped) {
      ElMessage.warning(`已跳过：${res.data.filename} 已在知识库中`)
    } else {
      ElMessage.success(`上传成功：${res.data.filename}，共 ${res.data.chunks_count} 个片段`)
    }
    await loadDocuments()
  } catch (err) {
    ElMessage.error('上传失败：' + err.message)
  }
  return false
}

const sendMessage = async () => {
  const query = inputText.value.trim()
  if (!query) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: query })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  // 创建 AI 回复占位
  const assistantMsg = { role: 'assistant', content: '', sources: null, queue: null }
  messages.value.push(assistantMsg)
  scrollToBottom()

  // SSE 连接：start_all.bat 串行启动，后端要十几秒才就绪，连不上先自动重连，
  // 每 2 秒一次、最多 15 次（约 30 秒宽限期），期间提示“正在连接服务”。
  const maxAttempts = 15
  let attempt = 0
  let retryTimer = null
  let evtSource = null

  const connect = () => {
    attempt += 1
    assistantMsg.queue = `正在连接服务（第 ${attempt}/${maxAttempts} 次）…`
    scrollToBottom()

    evtSource = new EventSource(getChatStream(query))

    evtSource.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'queue') {
        assistantMsg.queue = data.message
        scrollToBottom()
      } else if (data.type === 'sources') {
        assistantMsg.sources = (data.sources || []).map(s => ({ ...s, expanded: false }))
        assistantMsg.queue = null
        scrollToBottom()
      } else if (data.type === 'token') {
        assistantMsg.content += data.content
        scrollToBottom()
      } else if (data.type === 'done') {
        evtSource.close()
        loading.value = false
      } else if (data.type === 'error') {
        assistantMsg.content = '出错了：' + data.message
        evtSource.close()
        loading.value = false
      }
    }

    evtSource.onerror = () => {
      evtSource.close()
      // 已收到部分内容则不再自动重连，避免内容错乱
      if (assistantMsg.content) {
        assistantMsg.queue = '连接中断，请重新发送'
        loading.value = false
        return
      }
      if (attempt >= maxAttempts) {
        loading.value = false
        assistantMsg.content = '连接失败：服务未就绪。请确认 start_all.bat 的四个窗口都启动后，重新发送。'
      } else {
        retryTimer = setTimeout(connect, 2000)
      }
    }
  }

  connect()
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  max-width: 800px;
  height: 90vh;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
}

.doc-list {
  padding: 6px 20px;
  font-size: 13px;
  color: #909399;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.doc-list-title {
  margin-right: 8px;
}

.doc-tag {
  margin-right: 8px;
  margin-bottom: 4px;
}

.doc-list-empty {
  color: #c0c4cc;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.message {
  margin-bottom: 16px;
}

.user-message .content {
  background: #409eff;
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 70%;
  margin-left: auto;
}

.assistant-message .content {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 70%;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.text {
  word-break: break-word;
  line-height: 1.6;
  font-size: 14px;
}

.text :deep(p) {
  margin: 0 0 8px;
}
.text :deep(p:last-child) {
  margin-bottom: 0;
}
.text :deep(h1),
.text :deep(h2),
.text :deep(h3),
.text :deep(h4) {
  margin: 12px 0 6px;
  font-weight: 600;
  line-height: 1.4;
}
.text :deep(h1) { font-size: 20px; }
.text :deep(h2) { font-size: 17px; }
.text :deep(h3) { font-size: 15px; }
.text :deep(h4) { font-size: 14px; }
.text :deep(ul),
.text :deep(ol) {
  margin: 4px 0 8px;
  padding-left: 22px;
}
.text :deep(li) {
  margin: 2px 0;
}
.text :deep(code) {
  background: #f2f3f5;
  border-radius: 3px;
  padding: 1px 5px;
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
}
.text :deep(pre) {
  background: #f6f8fa;
  border-radius: 6px;
  padding: 10px 12px;
  overflow-x: auto;
  margin: 8px 0;
}
.text :deep(pre code) {
  background: none;
  padding: 0;
}
.text :deep(blockquote) {
  border-left: 3px solid #d0d7de;
  margin: 8px 0;
  padding: 2px 12px;
  color: #57606a;
}
.text :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}
.text :deep(th),
.text :deep(td) {
  border: 1px solid #d0d7de;
  padding: 4px 8px;
}
.text :deep(a) {
  color: #409eff;
}
.text :deep(hr) {
  border: none;
  border-top: 1px solid #e5e6eb;
  margin: 10px 0;
}

.sources {
  margin-bottom: 8px;
}

.source-item {
  margin-top: 6px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.source-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  font-size: 12px;
  color: #606266;
  background: #f5f7fa;
  cursor: pointer;
  user-select: none;
}

.source-head:hover {
  background: #eef1f6;
}

.source-name {
  font-weight: 600;
  color: #409eff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-meta {
  color: #909399;
  flex-shrink: 0;
}

.source-score {
  margin-left: auto;
  color: #67c23a;
  flex-shrink: 0;
}

.source-toggle {
  color: #909399;
  flex-shrink: 0;
}

.source-text {
  padding: 6px 8px;
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
  max-height: 180px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #fff;
}

.queue-info {
  margin-top: 8px;
  color: #e6a23c;
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-area .el-textarea {
  flex: 1;
}
</style>
