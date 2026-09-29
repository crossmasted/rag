import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器：自动附带 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 时清除登录态并跳转登录
api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
    }
    return Promise.reject(error)
  }
)

// ---- 认证 ----
export const register = (username, password) =>
  api.post('/auth/register', { username, password })

export const login = (username, password) =>
  api.post('/auth/login', { username, password }).then((res) => {
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    return res.data
  })

export const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export const getCurrentUser = () => {
  const raw = localStorage.getItem('user')
  return raw ? JSON.parse(raw) : null
}

// ---- 文档 ----
export const uploadDocument = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/documents/upload', formData)
}

export const listDocuments = () => api.get('/documents/list')

export const deleteDocument = (docId) => api.delete(`/documents/${encodeURIComponent(docId)}`)

// ---- 聊天 ----
export const getChatStream = (query) => {
  return `/api/chat/stream?query=${encodeURIComponent(query)}`
}

export default api
