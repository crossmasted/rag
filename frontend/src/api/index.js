import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const uploadDocument = (file, accessLevel = 'public') => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('access_level', accessLevel)
  return api.post('/documents/upload', formData)
}

export const listDocuments = () => api.get('/documents/list')

export const getChatStream = (query, accessLevel = 'public') => {
  return `/api/chat/stream?query=${encodeURIComponent(query)}&access_level=${accessLevel}`
}

export default api
