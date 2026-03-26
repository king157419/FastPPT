import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function uploadFile(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await api.post('/upload', form)
  return res.data
}

export async function uploadAudio(blob) {
  const form = new FormData()
  form.append('file', blob, 'recording.wav')
  const res = await api.post('/asr', form)
  return res.data  // { text: '...' }
}

export async function sendChat(messages) {
  const res = await api.post('/chat', { messages })
  return res.data
}

// 启动异步生成，返回 job_id
export async function startGenerate(intent, fileIds) {
  const res = await api.post('/generate/start', { intent, file_ids: fileIds })
  return res.data  // { job_id }
}

// 同步生成（备用）
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

// SSE 进度流 URL
export function generateStreamUrl(jobId) {
  return `/api/generate/${jobId}/stream`
}
