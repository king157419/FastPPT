import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

const PPTX_KEYS = ['pptx', 'pptx_file', 'pptx_filename', 'pptx_path', 'output_pptx', 'generated_pptx']
const DOCX_KEYS = ['docx', 'docx_file', 'docx_filename']

function pickFirstString(payload, keys) {
  if (!payload || typeof payload !== 'object') return ''
  for (const key of keys) {
    const value = payload[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

function looksLikeExt(filename, ext) {
  return typeof filename === 'string' && filename.toLowerCase().endsWith(ext)
}

export function extractSlidesJson(payload) {
  if (!payload || typeof payload !== 'object') return null

  if (payload.slides_json && typeof payload.slides_json === 'object') return payload.slides_json
  if (payload.slidesJson && typeof payload.slidesJson === 'object') return payload.slidesJson
  if (payload.result?.slides_json && typeof payload.result.slides_json === 'object') return payload.result.slides_json
  if (payload.data?.slides_json && typeof payload.data.slides_json === 'object') return payload.data.slides_json

  if (Array.isArray(payload.pages)) {
    return {
      theme: payload.theme || {},
      pages: payload.pages,
      meta: payload.meta || {},
    }
  }
  return null
}

export function extractPptxFilename(payload) {
  const fromKnownKeys = pickFirstString(payload, PPTX_KEYS)
  if (fromKnownKeys && looksLikeExt(fromKnownKeys, '.pptx')) return fromKnownKeys

  const generic = pickFirstString(payload, ['file', 'filename', 'output_file'])
  if (looksLikeExt(generic, '.pptx')) return generic

  return ''
}

export function extractDocxFilename(payload) {
  const fromKnownKeys = pickFirstString(payload, DOCX_KEYS)
  if (fromKnownKeys && looksLikeExt(fromKnownKeys, '.docx')) return fromKnownKeys

  const generic = pickFirstString(payload, ['file', 'filename', 'output_file'])
  if (looksLikeExt(generic, '.docx')) return generic

  return ''
}

export function normalizeGenerateResult(payload = {}) {
  const slides_json = extractSlidesJson(payload)
  const pptx = extractPptxFilename(payload)
  const docx = extractDocxFilename(payload)
  return {
    ...payload,
    slides_json: slides_json || payload.slides_json || null,
    pptx: pptx || payload.pptx || '',
    docx: docx || payload.docx || '',
    message: payload.message || payload.msg || '',
  }
}

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
  return normalizeGenerateResult(res.data)
}

export async function modifyCourse(payload) {
  const endpoints = [
    '/generate/revise',
    '/generate/modify',
    '/modify',
    '/ppt/modify',
    '/agent/modify',
    '/agent/generate/modify',
  ]

  let lastError = null
  for (const path of endpoints) {
    try {
      const res = await api.post(path, payload)
      return normalizeGenerateResult(res.data)
    } catch (err) {
      const status = err?.response?.status
      if (status === 404 || status === 405) {
        lastError = err
        continue
      }
      throw err
    }
  }

  if (lastError) throw lastError
  throw new Error('modify endpoint unavailable')
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
