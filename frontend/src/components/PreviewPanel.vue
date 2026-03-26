<template>
  <div class="preview-panel">
    <div class="preview-header">
      <span class="preview-title">🖼️ PPT 预览</span>
      <span v-if="slides.length" class="slide-count">共 {{ slides.length }} 页</span>
    </div>

    <div v-if="!slides.length && !loading" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-text">生成课件后，预览将显示在此处</div>
    </div>

    <div v-if="loading" class="loading-state">
      <el-icon class="spin"><Loading /></el-icon>
      <span>正在生成预览...</span>
    </div>

    <div v-if="slides.length" class="slides-container">
      <div
        v-for="s in slides"
        :key="s.page"
        class="slide-thumb"
        :class="{ active: currentPage === s.page }"
        @click="currentPage = s.page"
      >
        <div class="page-num">{{ s.page }}</div>
        <img :src="s.image" :alt="`第${s.page}页`" class="thumb-img" />
      </div>
    </div>

    <div v-if="currentSlide" class="slide-main">
      <img :src="currentSlide.image" :alt="`第${currentPage}页`" class="main-img" />
      <div class="nav-btns">
        <el-button size="small" :disabled="currentPage <= 1" @click="currentPage--">
          <el-icon><ArrowLeft /></el-icon> 上一页
        </el-button>
        <span class="page-info">{{ currentPage }} / {{ slides.length }}</span>
        <el-button size="small" :disabled="currentPage >= slides.length" @click="currentPage++">
          下一页 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getPreview } from '../api/index.js'
import { ElMessage } from 'element-plus'

const props = defineProps({ pptxFilename: String })

const slides = ref([])
const currentPage = ref(1)
const loading = ref(false)

const currentSlide = computed(() => slides.value.find(s => s.page === currentPage.value))

watch(() => props.pptxFilename, async (fn) => {
  if (!fn) return
  loading.value = true
  slides.value = []
  currentPage.value = 1
  try {
    const data = await getPreview(fn)
    slides.value = data.slides
  } catch (e) {
    ElMessage.error('预览加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.preview-panel {
  height: 100%; display: flex; flex-direction: column; gap: 12px;
  background: #111122; border-radius: 12px; padding: 16px;
}
.preview-header { display: flex; justify-content: space-between; align-items: center; }
.preview-title { font-size: 15px; font-weight: 600; color: #e0e0f0; }
.slide-count { font-size: 12px; color: #909399; }
.empty-state {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; color: #555577;
}
.empty-icon { font-size: 48px; }
.empty-text { font-size: 14px; }
.loading-state {
  flex: 1; display: flex; align-items: center; justify-content: center;
  gap: 10px; color: #909399; font-size: 14px;
}
.spin { animation: spin 1s linear infinite; font-size: 24px; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.slides-container {
  display: flex; gap: 8px; overflow-x: auto; padding-bottom: 8px;
  flex-shrink: 0;
}
.slide-thumb {
  flex-shrink: 0; cursor: pointer; border-radius: 6px;
  border: 2px solid transparent; transition: border-color 0.2s;
  position: relative;
}
.slide-thumb.active { border-color: #0f3a7a; }
.slide-thumb:hover { border-color: #5b8cf0; }
.page-num {
  position: absolute; top: 2px; left: 4px; font-size: 10px;
  color: #ffd700; background: rgba(0,0,0,0.5); padding: 0 3px; border-radius: 3px;
}
.thumb-img { width: 120px; height: 68px; object-fit: cover; border-radius: 4px; display: block; }
.slide-main { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.main-img { width: 100%; border-radius: 8px; border: 1px solid #2a2a4e; }
.nav-btns { display: flex; align-items: center; gap: 12px; }
.page-info { font-size: 13px; color: #909399; min-width: 50px; text-align: center; }
</style>
