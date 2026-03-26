<template>
  <div class="upload-area">
    <div class="section-label">📎 参考资料</div>

    <div
      class="drop-zone"
      :class="{ dragging: isDragging, hasFiles: files.length > 0 }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="handleDrop"
      @click="triggerInput"
    >
      <input ref="fileInput" type="file" multiple accept=".pdf,.docx,.doc,.pptx,.ppt,.txt,.md" style="display:none" @change="handleInputChange" />
      <div class="drop-icon">⬆</div>
      <div class="drop-text">拖拽文件或 <em>点击上传</em></div>
      <div class="drop-hint">PDF · Word · PPT · TXT，≤ 200MB</div>
    </div>

    <TransitionGroup name="file-list" tag="div" class="file-list" v-if="files.length > 0">
      <div v-for="f in files" :key="f.uid" class="file-item" :class="f.status">
        <span class="file-type-icon">{{ extIcon(f.name) }}</span>
        <span class="file-name">{{ f.name }}</span>
        <span class="file-status">
          <span v-if="f.status === 'uploading'" class="status-uploading">
            <span class="spinner"></span> 解析中
          </span>
          <span v-else-if="f.status === 'done'" class="status-done">✓ {{ f.chunkCount }}块</span>
          <span v-else-if="f.status === 'error'" class="status-error">✕ 失败</span>
          <span v-else class="status-pending">待上传</span>
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

const EXT_ICONS = { pdf: '📄', docx: '📝', doc: '📝', pptx: '📊', ppt: '📊', txt: '📃', md: '📃' }
function extIcon(name) {
  const ext = name.split('.').pop().toLowerCase()
  return EXT_ICONS[ext] || '📁'
}

function triggerInput() { fileInput.value?.click() }

function handleInputChange(e) {
  [...e.target.files].forEach(processFile)
  e.target.value = ''
}

function handleDrop(e) {
  isDragging.value = false
  ;[...e.dataTransfer.files].forEach(processFile)
}

async function processFile(raw) {
  const uid = Date.now() + Math.random()
  const entry = { uid, name: raw.name, status: 'uploading', chunkCount: 0, fileId: null }
  files.value.push(entry)
  try {
    const data = await uploadFile(raw)
    entry.status = 'done'
    entry.chunkCount = data.chunk_count
    entry.fileId = data.file_id
    ElMessage.success(`「${raw.name}」解析完成，${data.chunk_count} 块已入库`)
    emit('uploaded', { fileId: data.file_id, summary: data.summary, filename: raw.name })
  } catch (e) {
    entry.status = 'error'
    ElMessage.error(`「${raw.name}」上传失败：${e.response?.data?.detail || e.message}`)
  }
}
</script>

<style scoped>
.upload-area { display: flex; flex-direction: column; gap: 8px; }
.section-label { font-size: 11px; font-weight: 600; color: rgba(226, 232, 248, 0.4); letter-spacing: 0.8px; text-transform: uppercase; padding: 0 2px; }

.drop-zone {
  position: relative; border-radius: 12px; padding: 18px 16px;
  cursor: pointer; text-align: center;
  background: rgba(79, 142, 247, 0.03);
  border: 1.5px dashed rgba(79, 142, 247, 0.25);
  transition: all 0.25s;
  background-image: none;
  animation: dash-move 20s linear infinite;
}
@keyframes dash-move {
  0% { border-dash-offset: 0; }
  100% { border-dash-offset: 40px; }
}
.drop-zone::before {
  content: '';
  position: absolute; inset: 0; border-radius: 12px;
  background: linear-gradient(135deg, rgba(79,142,247,0.04), rgba(124,58,237,0.02));
  opacity: 0; transition: opacity 0.25s;
}
.drop-zone:hover::before, .drop-zone.dragging::before { opacity: 1; }
.drop-zone.dragging {
  border-color: rgba(79, 142, 247, 0.6);
  box-shadow: 0 0 20px rgba(79, 142, 247, 0.15), inset 0 0 20px rgba(79, 142, 247, 0.05);
}
.drop-zone:hover { border-color: rgba(79, 142, 247, 0.45); }

.drop-icon { font-size: 22px; margin-bottom: 6px; opacity: 0.6; }
.drop-text { font-size: 13px; color: rgba(226, 232, 248, 0.5); }
.drop-text em { color: #4F8EF7; font-style: normal; font-weight: 500; }
.drop-hint { font-size: 11px; color: rgba(226, 232, 248, 0.25); margin-top: 4px; }

.file-list { display: flex; flex-direction: column; gap: 5px; }
.file-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; border-radius: 8px;
  border: 1px solid rgba(79, 142, 247, 0.1);
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s;
}
.file-item.done { border-color: rgba(74, 222, 128, 0.2); background: rgba(74, 222, 128, 0.03); }
.file-item.error { border-color: rgba(239, 68, 68, 0.2); background: rgba(239, 68, 68, 0.03); }

.file-type-icon { font-size: 15px; flex-shrink: 0; }
.file-name { flex: 1; font-size: 12px; color: rgba(226, 232, 248, 0.7); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.file-status { flex-shrink: 0; font-size: 11px; }
.status-uploading { display: flex; align-items: center; gap: 5px; color: #4F8EF7; }
.spinner {
  width: 10px; height: 10px; border-radius: 50%;
  border: 1.5px solid rgba(79,142,247,0.3);
  border-top-color: #4F8EF7;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.status-done { color: #4ade80; font-weight: 600; }
.status-error { color: #f87171; }
.status-pending { color: rgba(226,232,248,0.3); }

.file-list-enter-active { transition: all 0.3s ease; }
.file-list-enter-from { opacity: 0; transform: translateY(-6px); }
</style>
