<template>
  <div class="generate-area">
    <el-button
      type="success"
      size="large"
      :disabled="!intentReady || generating"
      :loading="generating"
      @click="handleGenerate"
      class="gen-btn"
    >
      <el-icon v-if="!generating"><MagicStick /></el-icon>
      {{ generating ? '生成中，请稍候...' : '生成课件 (PPT + Word)' }}
    </el-button>
    <div v-if="!intentReady" class="hint">请先完成上方对话，收集教学意图</div>
    <div v-if="result" class="result-bar">
      <span class="result-msg">{{ result.message }}</span>
      <div class="dl-btns">
        <el-button type="primary" size="small" :href="pptxUrl" tag="a" :download="result.pptx">
          <el-icon><Download /></el-icon> 下载 PPT
        </el-button>
        <el-button type="info" size="small" :href="docxUrl" tag="a" :download="result.docx">
          <el-icon><Download /></el-icon> 下载 Word
        </el-button>
      </div>
    </div>
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
.generate-area { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.gen-btn { width: 100%; font-size: 15px; height: 44px; }
.hint { font-size: 12px; color: #909399; text-align: center; }
.result-bar {
  background: #0d1f0d; border: 1px solid #2d4a2d; border-radius: 8px;
  padding: 12px 16px; display: flex; flex-direction: column; gap: 10px;
}
.result-msg { font-size: 13px; color: #95d475; }
.dl-btns { display: flex; gap: 10px; }
</style>
