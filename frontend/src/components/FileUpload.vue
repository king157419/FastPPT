<template>
  <div class="upload-area">
    <div class="panel-header">
      <div class="panel-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" stroke="#0D9488" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>参考资料</span>
      </div>
      <span class="file-count" v-if="files.length">{{ files.length }} 个文件</span>
    </div>

    <div
      class="drop-zone"
      :class="{ dragging: isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="handleDrop"
      @click="triggerInput"
    >
      <input ref="fileInput" type="file" multiple accept=".pdf,.docx,.doc,.pptx,.ppt,.txt,.md,.jpg,.jpeg,.png,.webp,.mp4,.mov,.avi,.mkv" style="display:none" @change="handleInputChange" />
      <div class="drop-icon">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <polyline points="17 8 12 3 7 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="drop-text">拖拽或 <em>点击上传</em></div>
      <div class="drop-hint">PDF · Word · PPT · TXT · 图片 · 视频</div>
    </div>

    <TransitionGroup name="file-list" tag="div" class="file-list" v-if="files.length > 0">
      <div v-for="f in files" :key="f.uid" class="file-item" :class="f.status">
        <div class="file-icon" :style="{ background: extColor(f.name) }">{{ extLabel(f.name) }}</div>
        <span class="file-name">{{ f.name }}</span>
        <span class="file-badge" :class="f.status">
          <span v-if="f.status === 'uploading'" class="spinner"></span>
          <span v-else-if="f.status === 'done'">✓</span>
          <span v-else-if="f.status === 'error'">✕</span>
        </span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadFile } from '../api/index.js'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['uploaded'])
const files = ref([])
const isDragging = ref(false)
const fileInput = ref(null)

const EXT_COLORS = {
  pdf: '#EF4444', docx: '#3B82F6', doc: '#3B82F6', pptx: '#F97316', ppt: '#F97316',
  txt: '#6B7280', md: '#8B5CF6',
  jpg: '#8B5CF6', jpeg: '#8B5CF6', png: '#8B5CF6', webp: '#8B5CF6', bmp: '#8B5CF6',
  mp4: '#059669', mov: '#059669', avi: '#059669', mkv: '#059669', webm: '#059669',
}
const EXT_LABELS = {
  pdf: 'PDF', docx: 'DOC', doc: 'DOC', pptx: 'PPT', ppt: 'PPT', txt: 'TXT', md: 'MD',
  jpg: 'IMG', jpeg: 'IMG', png: 'IMG', webp: 'IMG', bmp: 'IMG',
  mp4: 'VID', mov: 'VID', avi: 'VID', mkv: 'VID', webm: 'VID',
}

function extColor(name) { return EXT_COLORS[name.split('.').pop().toLowerCase()] || '#9CA3AF' }
function extLabel(name) { return EXT_LABELS[name.split('.').pop().toLowerCase()] || 'FILE' }
function triggerInput() { fileInput.value?.click() }

function handleInputChange(e) { [...e.target.files].forEach(processFile) }
function handleDrop(e) { isDragging.value = false; [...e.dataTransfer.files].forEach(processFile) }

async function processFile(file) {
  const uid = Date.now() + Math.random()
  files.value.push({ uid, name: file.name, status: 'uploading', chunkCount: 0 })
  try {
    const data = await uploadFile(file)
    const f = files.value.find(f => f.uid === uid)
    if (f) { f.status = 'done'; f.chunkCount = data.chunk_count || 0 }
    emit('uploaded', { fileId: data.file_id, summary: data.summary, filename: file.name })
  } catch (e) {
    const f = files.value.find(f => f.uid === uid)
    if (f) f.status = 'error'
    ElMessage.error('上传失败：' + (e.response?.data?.detail || e.message))
  }
}
</script>

<style scoped>
.upload-area {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.panel-title {
  display: flex; align-items: center; gap: 7px;
  font-size: 13px; font-weight: 600; color: var(--text);
}
.file-count {
  font-size: 11px; color: var(--text-3);
  background: #F3F4F6; padding: 2px 8px; border-radius: 99px;
}
.drop-zone {
  margin: 12px; border-radius: var(--radius-sm);
  border: 1.5px dashed var(--border);
  padding: 20px 16px;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  cursor: pointer; transition: all 0.2s;
  color: var(--text-3);
}
.drop-zone:hover, .drop-zone.dragging {
  border-color: var(--teal);
  background: var(--teal-light);
  color: var(--teal);
}
.drop-icon { font-size: 22px; margin-bottom: 4px; }
.drop-text { font-size: 13px; font-weight: 500; color: var(--text-2); }
.drop-text em { color: var(--teal); font-style: normal; font-weight: 600; }
.drop-hint { font-size: 11px; color: var(--text-3); }
.file-list { display: flex; flex-direction: column; gap: 4px; padding: 0 12px 12px; }
.file-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; border-radius: var(--radius-sm);
  background: var(--bg); border: 1px solid var(--border);
  transition: all 0.2s;
}
.file-item.done { border-color: #D1FAE5; background: #F0FDF4; }
.file-item.error { border-color: #FEE2E2; background: #FFF5F5; }
.file-icon {
  width: 28px; height: 20px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 8px; font-weight: 700; color: white; flex-shrink: 0;
  letter-spacing: 0.3px;
}
.file-name {
  flex: 1; font-size: 12px; color: var(--text-2);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.file-badge {
  width: 20px; height: 20px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.file-badge.done { background: #D1FAE5; color: #059669; }
.file-badge.error { background: #FEE2E2; color: #DC2626; }
.file-badge.uploading { background: var(--teal-light); }
.spinner {
  width: 10px; height: 10px; border-radius: 50%;
  border: 1.5px solid rgba(13,148,136,0.3);
  border-top-color: var(--teal);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.file-list-enter-active { transition: all 0.25s ease; }
.file-list-enter-from { opacity: 0; transform: translateY(-4px); }
</style>
