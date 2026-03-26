<template>
  <div class="generate-area">
    <button
      class="gen-btn"
      :class="{ loading: generating, ready: intentReady && !generating }"
      :disabled="!intentReady || generating"
      @click="handleGenerate"
    >
      <span class="btn-glow"></span>
      <span class="btn-content">
        <span v-if="generating" class="btn-spinner"></span>
        <span v-else class="btn-icon">✦</span>
        {{ generating ? '正在生成课件...' : '生成课件 (PPT + Word)' }}
      </span>
    </button>

    <p v-if="!intentReady" class="hint">完成上方对话后解锁</p>

    <Transition name="result-fade">
      <div v-if="result" class="result-card">
        <div class="result-header">
          <span class="result-icon">🎉</span>
          <span class="result-msg">{{ result.message }}</span>
        </div>
        <div class="dl-row">
          <a class="dl-btn ppt" :href="pptxUrl" :download="result.pptx">
            <span class="dl-icon">📊</span>
            <span class="dl-label">下载 PPT</span>
          </a>
          <a class="dl-btn word" :href="docxUrl" :download="result.docx">
            <span class="dl-icon">📝</span>
            <span class="dl-label">下载 Word</span>
          </a>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { generateCourse, downloadUrl } from '../api/index.js'
import { ElMessage } from 'element-plus'

const props = defineProps({
  intentReady: Boolean,
  intent: Object,
  fileIds: Array,
})
const emit = defineEmits(['generated'])
const generating = ref(false)
const result = ref(null)

const pptxUrl = computed(() => result.value ? downloadUrl(result.value.pptx) : '#')
const docxUrl = computed(() => result.value ? downloadUrl(result.value.docx) : '#')

async function handleGenerate() {
  generating.value = true
  result.value = null
  try {
    const data = await generateCourse(props.intent, props.fileIds || [])
    result.value = data
    ElMessage.success(data.message)
    emit('generated', data)
  } catch (e) {
    ElMessage.error('生成失败：' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.generate-area { display: flex; flex-direction: column; gap: 10px; }

.gen-btn {
  position: relative; width: 100%; height: 48px;
  border: none; border-radius: 12px; cursor: pointer;
  font-size: 14px; font-weight: 600; letter-spacing: 0.3px;
  color: rgba(226, 232, 248, 0.4);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  transition: all 0.3s; overflow: hidden;
  font-family: inherit;
}
.gen-btn.ready {
  background: linear-gradient(135deg, #4F8EF7 0%, #7C3AED 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 4px 20px rgba(79, 142, 247, 0.25);
}
.gen-btn.ready:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(79, 142, 247, 0.45);
}
.gen-btn.ready:hover .btn-glow {
  opacity: 1;
}
.gen-btn:disabled:not(.loading) { cursor: not-allowed; }
.gen-btn.loading {
  background: linear-gradient(135deg, rgba(79,142,247,0.4), rgba(124,58,237,0.4));
  border-color: transparent; color: rgba(255,255,255,0.7);
  cursor: wait;
}

.btn-glow {
  position: absolute; inset: -1px; border-radius: 12px;
  background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent, rgba(255,255,255,0.05));
  opacity: 0; transition: opacity 0.3s; pointer-events: none;
}
.btn-content { position: relative; display: flex; align-items: center; justify-content: center; gap: 8px; }
.btn-icon { font-size: 16px; }
.btn-spinner {
  width: 16px; height: 16px; border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.hint { font-size: 11px; color: rgba(226,232,248,0.25); text-align: center; }

.result-card {
  border-radius: 12px; overflow: hidden;
  border: 1px solid rgba(74, 222, 128, 0.2);
  background: rgba(74, 222, 128, 0.04);
}
.result-header {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(74, 222, 128, 0.1);
}
.result-icon { font-size: 16px; }
.result-msg { font-size: 12px; color: #4ade80; font-weight: 500; }

.dl-row { display: flex; gap: 8px; padding: 10px 12px; }
.dl-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 9px 12px; border-radius: 8px;
  font-size: 12px; font-weight: 600; text-decoration: none;
  transition: all 0.2s; cursor: pointer;
}
.dl-btn.ppt {
  background: rgba(79, 142, 247, 0.12);
  border: 1px solid rgba(79, 142, 247, 0.25);
  color: #4F8EF7;
}
.dl-btn.ppt:hover {
  background: rgba(79, 142, 247, 0.22);
  box-shadow: 0 0 12px rgba(79,142,247,0.2);
}
.dl-btn.word {
  background: rgba(255, 215, 0, 0.08);
  border: 1px solid rgba(255, 215, 0, 0.2);
  color: #FFD700;
}
.dl-btn.word:hover {
  background: rgba(255, 215, 0, 0.15);
  box-shadow: 0 0 12px rgba(255,215,0,0.15);
}
.dl-icon { font-size: 15px; }

.result-fade-enter-active { transition: all 0.4s ease; }
.result-fade-enter-from { opacity: 0; transform: translateY(8px); }
</style>
