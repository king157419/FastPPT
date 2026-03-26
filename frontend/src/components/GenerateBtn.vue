<template>
  <div class="generate-area">
    <button
      class="gen-btn"
      :class="{ loading: generating, ready: intentReady && !generating }"
      :disabled="!intentReady || generating"
      @click="handleGenerate"
    >
      <span v-if="generating" class="btn-spinner"></span>
      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      {{ generating ? progressMsg || '正在生成课件...' : '生成课件' }}
    </button>
    <p v-if="!intentReady" class="hint">完成对话后解锁</p>

    <Transition name="result-fade">
      <div v-if="generating" class="progress-bar-wrap">
        <div class="progress-bar" :style="{ width: progress + '%' }"></div>
        <span class="progress-text">{{ progress }}%</span>
      </div>
    </Transition>

    <Transition name="result-fade">
      <div v-if="result" class="result-card">
        <div class="result-header">
          <span class="result-icon">🎉</span>
          <span class="result-msg">{{ result.message }}</span>
        </div>
        <div class="dl-row">
          <a class="dl-btn" :href="docxUrl" :download="result.docx">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            下载 Word 教案
          </a>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { startGenerate, generateCourse, downloadUrl, generateStreamUrl } from '../api/index.js'
import { ElMessage } from 'element-plus'

const props = defineProps({
  intentReady: Boolean,
  intent: Object,
  fileIds: Array,
})
const emit = defineEmits(['generated'])
const generating = ref(false)
const progress = ref(0)
const progressMsg = ref('')
const result = ref(null)

const docxUrl = computed(() => result.value ? downloadUrl(result.value.docx) : '#')

async function handleGenerate() {
  generating.value = true
  result.value = null
  progress.value = 0
  progressMsg.value = '准备中...'

  try {
    // 尝试异步 SSE 模式
    const { job_id } = await startGenerate(props.intent, props.fileIds || [])
    await new Promise((resolve, reject) => {
      const es = new EventSource(generateStreamUrl(job_id))
      es.onmessage = (e) => {
        const data = JSON.parse(e.data)
        progress.value = data.progress || 0
        progressMsg.value = data.message || ''
        if (data.done) {
          es.close()
          if (data.error) { reject(new Error(data.error)); return }
          result.value = { slides_json: data.slides_json, docx: data.docx, message: '课件生成成功！' }
          emit('generated', result.value)
          ElMessage.success('课件生成成功！')
          resolve()
        }
      }
      es.onerror = () => { es.close(); reject(new Error('SSE 连接失败')) }
    })
  } catch (e) {
    // fallback 同步模式
    try {
      progressMsg.value = '正在生成...'
      const data = await generateCourse(props.intent, props.fileIds || [])
      result.value = data
      progress.value = 100
      ElMessage.success(data.message)
      emit('generated', data)
    } catch (e2) {
      ElMessage.error('生成失败：' + (e2.response?.data?.detail || e2.message))
    }
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.generate-area { display: flex; flex-direction: column; gap: 8px; }

.gen-btn {
  width: 100%; height: 46px;
  border: none; border-radius: var(--radius);
  cursor: pointer; font-size: 14px; font-weight: 600;
  font-family: inherit; letter-spacing: 0.1px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
  transition: all 0.25s;
  background: #E5E7EB; color: #9CA3AF;
}
.gen-btn.ready {
  background: var(--teal); color: white;
  box-shadow: 0 4px 14px rgba(13,148,136,0.3);
}
.gen-btn.ready:hover {
  background: #0F766E;
  box-shadow: 0 6px 20px rgba(13,148,136,0.4);
  transform: translateY(-1px);
}
.gen-btn.loading {
  background: var(--teal-light); color: var(--teal); cursor: wait;
}
.gen-btn:disabled:not(.loading) { cursor: not-allowed; }
.btn-spinner {
  width: 16px; height: 16px; border-radius: 50%;
  border: 2px solid rgba(13,148,136,0.3);
  border-top-color: var(--teal);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.hint { font-size: 11px; color: var(--text-3); text-align: center; }

.progress-bar-wrap {
  position: relative; height: 6px;
  background: var(--border); border-radius: 99px; overflow: hidden;
}
.progress-bar {
  height: 100%; background: var(--teal);
  border-radius: 99px; transition: width 0.4s ease;
}
.progress-text {
  position: absolute; right: 0; top: -18px;
  font-size: 11px; color: var(--teal); font-weight: 600;
}

.result-card {
  border-radius: var(--radius); overflow: hidden;
  border: 1px solid #D1FAE5;
  background: #F0FDF4;
}
.result-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid #D1FAE5;
}
.result-icon { font-size: 15px; }
.result-msg { font-size: 12px; color: #059669; font-weight: 500; }

.dl-row { padding: 10px 12px; }
.dl-btn {
  display: flex; align-items: center; justify-content: center; gap: 7px;
  padding: 9px 14px; border-radius: var(--radius-sm);
  font-size: 12px; font-weight: 600; text-decoration: none;
  background: white; border: 1px solid #D1FAE5;
  color: #059669; transition: all 0.2s; width: 100%;
}
.dl-btn:hover { background: #D1FAE5; }

.result-fade-enter-active { transition: all 0.35s ease; }
.result-fade-enter-from { opacity: 0; transform: translateY(6px); }
</style>
