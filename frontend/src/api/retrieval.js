import axios from 'axios'

const retrievalApi = axios.create({
  baseURL: '/api/retrieval',
  timeout: 120000,
})

export async function uploadRetrievalDocument(file, options = {}) {
  const form = new FormData()
  form.append('file', file)
  if (options.kbId) form.append('kb_id', options.kbId)
  form.append('parser', options.parser || 'layout_aware')

  const res = await retrievalApi.post('/upload', form)
  return res.data
}

export async function searchKnowledge(query, options = {}) {
  const payload = {
    query,
    kb_ids: options.kbIds || [],
    top_k: options.topK ?? 5,
    similarity_threshold: options.similarityThreshold ?? 0.7,
    rerank: options.rerank ?? true,
  }
  const res = await retrievalApi.post('/search', payload)
  return res.data
}

export async function listRetrievalDocuments(kbId) {
  const params = kbId ? { kb_id: kbId } : undefined
  const res = await retrievalApi.get('/documents', { params })
  return res.data
}

export async function deleteRetrievalDocument(docId) {
  const res = await retrievalApi.delete(`/documents/${encodeURIComponent(docId)}`)
  return res.data
}

