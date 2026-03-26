<template>
  <div class="upload-area">
    <div class="upload-label">📎 上传参考资料</div>
    <el-upload
      class="upload-dragger"
      drag
      multiple
      :auto-upload="false"
      :on-change="handleChange"
      :show-file-list="false"
      accept=".pdf,.docx,.doc,.pptx,.ppt,.txt,.md"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处，或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">支持 PDF / Word / PPT / TXT，单文件 ≤ 200MB</div>
      </template>
    </el-upload>

    <div v-if="files.length > 0" class="file-list">
      <div v-for="f in files" :key="f.uid" class="file-item">
        <span class="file-icon">{{ extIcon(f.name) }}</span>
        <span class="file-name">{{ f.name }}</span>
        <el-tag v-if="f.status === 'uploading'" type="warning" size="small">解析中...</el-tag>
        <el-tag v-else-if="f.status === 'done'" type="success" size="small">已入库 {{ f.chunkCount }} 块</el-tag>
        <el-tag v-else-if="f.status === 'error'" type="danger" size="small">失败</el-tag>
        <el-tag v-else size="small">等待上传</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadFile } from '../api/index.js'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['uploaded'])
const files = ref([])

function extIcon(name) {
  const ext = name.split('.').pop().toLowerCase()
  const map = { pdf: '📄', docx: '📝', doc: '📝', pptx: '📊', ppt: '📊', txt: '📃', md: '📃' }
  return map[ext] || '📁'
}

async function handleChange(file) {
  const entry = { uid: file.uid, name: file.name, status: 'uploading', chunkCount: 0, fileId: null }
  files.value.push(entry)
  try {
    const data = await uploadFile(file.raw)
    entry.status = 'done'
    entry.chunkCount = data.chunk_count
    entry.fileId = data.file_id
    ElMessage.success(`「${file.name}」解析完成，${data.chunk_count} 个文本块已入库`)
    emit('uploaded', { fileId: data.file_id, summary: data.summary, filename: file.name })
  } catch (e) {
    entry.status = 'error'
    ElMessage.error(`「${file.name}」上传失败：${e.response?.data?.detail || e.message}`)
  }
}
</script>

<style scoped>
.upload-area { margin-bottom: 12px; }
.upload-label { font-size: 13px; color: #909399; margin-bottom: 6px; font-weight: 500; }
.upload-dragger { width: 100%; }
.file-list { margin-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.file-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; background: #1a1a2e; border-radius: 6px;
  border: 1px solid #2a2a4e;
}
.file-icon { font-size: 16px; }
.file-name { flex: 1; font-size: 13px; color: #c0c4cc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
