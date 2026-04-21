<template>
  <div class="doc-panel">
    <div class="panel-header">
      <div class="panel-title">
        <span>知识库文档</span>
      </div>
      <button class="small-btn" @click="refreshDocuments" :disabled="loadingDocs">
        刷新
      </button>
    </div>

    <div class="upload-row">
      <input
        ref="fileInput"
        type="file"
        class="hidden-input"
        @change="onFileSelected"
      />
      <button class="upload-btn" @click="triggerPick" :disabled="uploading">
        {{ uploading ? '上传中...' : '上传文档' }}
      </button>
      <span class="upload-tip">支持 PDF / Word / TXT</span>
    </div>

    <div class="doc-list-wrap">
      <div v-if="loadingDocs" class="empty-line">正在加载文档...</div>
      <div v-else-if="!documents.length" class="empty-line">暂无知识库文档</div>
      <div v-else class="doc-list">
        <div v-for="doc in documents" :key="doc.id || doc.doc_id || doc.name" class="doc-item">
          <div class="doc-main">
            <div class="doc-name">{{ doc.name || doc.filename || doc.doc_id || doc.id }}</div>
            <div class="doc-meta">
              <span>{{ doc.status || 'indexed' }}</span>
              <span v-if="doc.chunk_count || doc.chunkCount">块数 {{ doc.chunk_count || doc.chunkCount }}</span>
            </div>
          </div>
          <button class="danger-btn" @click="removeDocument(doc)" :disabled="deletingId === (doc.id || doc.doc_id)">
            删除
          </button>
        </div>
      </div>
    </div>

    <div class="search-row">
      <input
        v-model="query"
        class="search-input"
        placeholder="检索知识点..."
        @keyup.enter="search"
      />
      <button class="small-btn" @click="search" :disabled="searching || !query.trim()">
        {{ searching ? '检索中' : '检索' }}
      </button>
    </div>

    <div class="search-result">
      <div v-if="searching" class="empty-line">正在检索...</div>
      <div v-else-if="results.length">
        <div v-for="(item, idx) in results" :key="idx" class="result-item">
          <div class="result-head">
            <div class="result-title">片段 {{ idx + 1 }}</div>
            <button class="insert-btn" @click="insertToChat(item)">插入对话</button>
          </div>
          <div class="result-content">{{ previewChunk(item) }}</div>
        </div>
      </div>
      <div v-else class="empty-line">输入关键词后可查看检索结果</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  uploadRetrievalDocument,
  listRetrievalDocuments,
  deleteRetrievalDocument,
  searchKnowledge,
} from '../api/retrieval.js'

const emit = defineEmits(['insertPrompt'])
const documents = ref([])
const loadingDocs = ref(false)
const uploading = ref(false)
const searching = ref(false)
const deletingId = ref('')
const query = ref('')
const results = ref([])
const fileInput = ref(null)

function previewChunk(item) {
  const text = item?.content || item?.text || item?.chunk || JSON.stringify(item)
  return String(text).slice(0, 220)
}

function insertToChat(item) {
  const text = item?.content || item?.text || item?.chunk
  if (!text) {
    ElMessage.warning('该片段为空，无法插入')
    return
  }
  emit('insertPrompt', String(text))
  ElMessage.success('已插入到对话输入框')
}

async function refreshDocuments() {
  loadingDocs.value = true
  try {
    const data = await listRetrievalDocuments()
    documents.value = data.documents || []
  } catch (e) {
    ElMessage.error(`文档列表获取失败：${e.response?.data?.detail || e.message}`)
  } finally {
    loadingDocs.value = false
  }
}

function triggerPick() {
  fileInput.value?.click()
}

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  uploading.value = true
  try {
    await uploadRetrievalDocument(file)
    ElMessage.success(`文档上传成功：${file.name}`)
    await refreshDocuments()
  } catch (e) {
    ElMessage.error(`文档上传失败：${e.response?.data?.detail || e.message}`)
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

async function removeDocument(doc) {
  const id = doc.id || doc.doc_id
  if (!id) {
    ElMessage.error('文档ID不存在，无法删除')
    return
  }
  if (!window.confirm('确认删除该文档？')) return

  deletingId.value = id
  try {
    await deleteRetrievalDocument(id)
    ElMessage.success('文档删除成功')
    await refreshDocuments()
  } catch (e) {
    ElMessage.error(`文档删除失败：${e.response?.data?.detail || e.message}`)
  } finally {
    deletingId.value = ''
  }
}

async function search() {
  const q = query.value.trim()
  if (!q) return

  searching.value = true
  try {
    const data = await searchKnowledge(q)
    results.value = data.chunks || []
  } catch (e) {
    ElMessage.error(`检索失败：${e.response?.data?.detail || e.message}`)
  } finally {
    searching.value = false
  }
}

onMounted(refreshDocuments)
</script>

<style scoped>
.doc-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.upload-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.hidden-input {
  display: none;
}
.upload-btn,
.small-btn,
.danger-btn {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: #fff;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}
.upload-btn:hover,
.small-btn:hover {
  border-color: var(--teal);
}
.upload-tip {
  font-size: 11px;
  color: var(--text-3);
}
.doc-list-wrap,
.search-result {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px;
  max-height: 180px;
  overflow-y: auto;
}
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.doc-item {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  background: #fafafa;
}
.doc-main {
  min-width: 0;
}
.doc-name {
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.doc-meta {
  margin-top: 3px;
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-3);
}
.danger-btn {
  color: #dc2626;
  border-color: #fecaca;
  background: #fef2f2;
}
.search-row {
  display: flex;
  gap: 8px;
}
.search-input {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0 10px;
  height: 34px;
  font-size: 12px;
  outline: none;
}
.search-input:focus {
  border-color: var(--teal);
}
.result-item {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 7px;
  background: #fafafa;
  margin-bottom: 6px;
}
.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.result-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--teal);
}
.insert-btn {
  border: 1px solid #99f6e4;
  color: #0f766e;
  background: #e6fffa;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 10px;
  cursor: pointer;
}
.result-content {
  font-size: 12px;
  color: var(--text-2);
  line-height: 1.4;
  white-space: pre-wrap;
}
.empty-line {
  font-size: 12px;
  color: var(--text-3);
  text-align: center;
  padding: 8px 4px;
}
</style>
