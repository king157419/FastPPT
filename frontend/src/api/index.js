import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/upload', form)
  return res.data
}

export async function sendChat(messages) {
  const res = await api.post('/chat', { messages })
  return res.data
}

export async function generateCourse(intent, fileIds) {
  const res = await api.post('/generate', { intent, file_ids: fileIds })
  return res.data
}

export async function getPreview(filename) {
  const res = await api.get(`/preview/${encodeURIComponent(filename)}`)
  return res.data
}

export function downloadUrl(filename) {
  return `/api/download/${encodeURIComponent(filename)}`
}
