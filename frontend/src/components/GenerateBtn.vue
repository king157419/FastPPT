<template>
  <div class="generate-area">
    <div v-if="intentReady" class="preflight-card">
      <div class="preflight-title">生成前确认</div>
      <div class="preflight-grid">
        <label class="field">
          <span>教学目标</span>
          <textarea
            v-model="teachingGoal"
            rows="2"
            placeholder="例如：理解XX概念，并能在XX问题中应用"
          />
        </label>
        <label class="field">
          <span>面向学生类型</span>
          <input
            v-model="audienceField"
            type="text"
            placeholder="例如：大一本科生"
          />
        </label>
        <label class="field">
          <span>重点难点</span>
          <input
            v-model="difficultyField"
            type="text"
            placeholder="例如：概念区分与公式应用"
          />
        </label>
      </div>
      <div v-if="missingFields.length" class="preflight-warning">
        缺少必填项：{{ missingFields.join('、') }}
      </div>
    </div>

    <button
      class="gen-btn"
      :class="{ loading: generating, ready: canGenerate }"
      :disabled="!canGenerate || generating"
      @click="handleGenerate"
    >
      <span v-if="generating" class="btn-spinner"></span>
      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      {{ generating ? progressMsg || '正在生成课件...' : '生成课件' }}
    </button>
    <p v-if="!intentReady" class="hint">完成对话后解锁</p>
    <p v-else-if="missingFields.length" class="hint warn">请先补齐生成前必填项</p>

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
          <span class="result-msg">{{ result.message || '课件生成成功' }}</span>
        </div>
        <div class="dl-row" v-if="pptxFilename || docxFilename">
          <a v-if="pptxFilename" class="dl-btn" :href="pptxUrl" :download="pptxFilename">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            下载 PPT 课件
          </a>
          <a v-if="docxFilename" class="dl-btn" :href="docxUrl" :download="docxFilename">
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
import { ref, computed, watch } from 'vue'
import { startGenerate, generateCourse, downloadUrl, generateStreamUrl, normalizeGenerateResult } from '../api/index.js'
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
const teachingGoal = ref('')
const audienceField = ref('')
const difficultyField = ref('')

const normalizedResult = computed(() => normalizeGenerateResult(result.value || {}))
const docxFilename = computed(() => normalizedResult.value.docx)
const pptxFilename = computed(() => normalizedResult.value.pptx)
const docxUrl = computed(() => docxFilename.value ? downloadUrl(docxFilename.value) : '#')
const pptxUrl = computed(() => pptxFilename.value ? downloadUrl(pptxFilename.value) : '#')

const missingFields = computed(() => {
  const missing = []
  if (!teachingGoal.value.trim()) missing.push('教学目标')
  if (!audienceField.value.trim()) missing.push('面向学生类型')
  if (!difficultyField.value.trim()) missing.push('重点难点')
  return missing
})
const canGenerate = computed(() => props.intentReady && missingFields.value.length === 0 && !generating.value)

watch(
  () => props.intent,
  (intent) => {
    teachingGoal.value = intent?.teaching_goal || ''
    audienceField.value = intent?.audience || ''
    difficultyField.value = intent?.difficulty_focus || ''
  },
  { immediate: true, deep: true },
)

function buildEffectiveIntent() {
  return {
    ...(props.intent || {}),
    teaching_goal: teachingGoal.value.trim(),
    audience: audienceField.value.trim(),
    difficulty_focus: difficultyField.value.trim(),
  }
}

function applyGenerateResult(payload) {
  const normalized = normalizeGenerateResult(payload)
  result.value = {
    ...normalized,
    message: normalized.message || '课件生成成功',
  }
  emit('generated', result.value)
}

async function handleGenerate() {
  if (missingFields.value.length) {
    ElMessage.warning(`请先补齐：${missingFields.value.join('、')}`)
    return
  }

  generating.value = true
  result.value = null
  progress.value = 0
  progressMsg.value = '准备中...'
  const effectiveIntent = buildEffectiveIntent()

  try {
    const { job_id } = await startGenerate(effectiveIntent, props.fileIds || [])
    await new Promise((resolve, reject) => {
      const es = new EventSource(generateStreamUrl(job_id))
      es.onmessage = (e) => {
        const data = JSON.parse(e.data)
        progress.value = data.progress || 0
        progressMsg.value = data.message || ''
        if (data.done) {
          es.close()
          if (data.error) {
            reject(new Error(data.error))
            return
          }
          applyGenerateResult(data)
          ElMessage.success('课件生成成功')
          resolve()
        }
      }
      es.onerror = () => {
        es.close()
        reject(new Error('SSE 连接失败'))
      }
    })
  } catch {
    try {
      progressMsg.value = '正在生成...'
      const data = await generateCourse(effectiveIntent, props.fileIds || [])
      applyGenerateResult(data)
      progress.value = 100
      ElMessage.success(result.value?.message || '课件生成成功')
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

.preflight-card {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: var(--radius);
  padding: 10px;
}
.preflight-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}
.preflight-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field span {
  font-size: 11px;
  color: var(--text-2);
}
.field input,
.field textarea {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 7px 9px;
  font-size: 12px;
  font-family: inherit;
  color: var(--text);
  outline: none;
  background: #fafafa;
}
.field input:focus,
.field textarea:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 2px rgba(13,148,136,0.1);
  background: #fff;
}
.preflight-warning {
  margin-top: 6px;
  font-size: 11px;
  color: #b45309;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 5px 8px;
}

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
.hint.warn { color: #b45309; }

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

.dl-row {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
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
