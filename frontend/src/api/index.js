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

export async function sendChat(messages, options = {}) {
  const payload = {
    messages,
    stream: Boolean(options.stream),
    use_agent: Boolean(options.useAgent),
  }
  if (options.sessionId) payload.session_id = options.sessionId

  const res = await api.post('/chat', payload)
  return res.data
}

export async function sendChatStream(messages, options = {}) {
  const payload = {
    messages,
    stream: true,
    use_agent: Boolean(options.useAgent),
  }
  if (options.sessionId) payload.session_id = options.sessionId

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }
  if (!response.body) throw new Error('流式响应为空')

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  const emit = async (event) => {
    if (typeof options.onEvent === 'function') await options.onEvent(event)
  }

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const events = buffer.split('\n\n')
    buffer = events.pop() || ''

    for (const block of events) {
      const line = block
        .split('\n')
        .map((item) => item.trim())
        .find((item) => item.startsWith('data:'))

      if (!line) continue
      const raw = line.slice(5).trim()
      if (!raw) continue

      try {
        await emit(JSON.parse(raw))
      } catch {
        await emit({ chunk: raw })
      }
    }
  }
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
