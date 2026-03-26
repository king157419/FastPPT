<template>
  <div class="preview-panel">
    <div class="preview-header">
      <span class="preview-title">🖼 PPT 预览</span>
      <span v-if="slides.length" class="slide-count">{{ slides.length }} 页</span>
    </div>

    <div v-if="!slides.length && !loading" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-title">暂无预览</div>
      <div class="empty-sub">生成课件后，幻灯片将显示在此处</div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="load-ring"></div>
      <span>正在渲染预览...</span>
    </div>

    <template v-if="slides.length">
      <!-- 缩略图条 -->
      <div class="thumb-strip">
        <div
          v-for="s in slides"
          :key="s.page"
          class="thumb"
          :class="{ active: currentPage === s.page }"
          @click="currentPage = s.page"
        >
          <img :src="s.image" :alt="`第${s.page}页`" class="thumb-img" />
          <span class="thumb-num">{{ s.page }}</span>
        </div>
      </div>

      <!-- 主视图 -->
      <div class="main-view">
        <Transition name="slide-fade" mode="out-in">
          <img
            v-if="currentSlide"
            :key="currentPage"
            :src="currentSlide.image"
            :alt="`第${currentPage}页`"
            class="main-img"
          />
        </Transition>
      </div>

      <!-- 导航 -->
      <div class="nav-bar">
        <button class="nav-btn" :disabled="currentPage <= 1" @click="currentPage--">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <span class="page-counter">
          <span class="page-cur">{{ currentPage }}</span>
          <span class="page-sep">/</span>
          <span class="page-total">{{ slides.length }}</span>
        </span>
        <button class="nav-btn" :disabled="currentPage >= slides.length" @click="currentPage++">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </template>
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
  height: 100%; display: flex; flex-direction: column; gap: 14px;
  background: rgba(10, 10, 30, 0.5);
  border: 1px solid rgba(79, 142, 247, 0.12);
  border-radius: 16px; padding: 16px;
  backdrop-filter: blur(10px);
}

.preview-header {
  display: flex; justify-content: space-between; align-items: center;
  flex-shrink: 0;
}
.preview-title { font-size: 13px; font-weight: 600; color: rgba(226,232,248,0.7); }
.slide-count {
  font-size: 11px; font-family: 'JetBrains Mono', monospace;
  color: #4F8EF7; background: rgba(79,142,247,0.1);
  border: 1px solid rgba(79,142,247,0.2);
  padding: 2px 8px; border-radius: 99px;
}

.empty-state {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; color: rgba(226,232,248,0.2);
}
.empty-icon { font-size: 52px; opacity: 0.4; }
.empty-title { font-size: 15px; font-weight: 500; color: rgba(226,232,248,0.3); }
.empty-sub { font-size: 12px; }

.loading-state {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 14px; color: rgba(226,232,248,0.4); font-size: 13px;
}
.load-ring {
  width: 32px; height: 32px; border-radius: 50%;
  border: 2px solid rgba(79,142,247,0.2);
  border-top-color: #4F8EF7;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.thumb-strip {
  display: flex; gap: 8px; overflow-x: auto; flex-shrink: 0;
  padding-bottom: 6px;
}
.thumb-strip::-webkit-scrollbar { height: 3px; }
.thumb-strip::-webkit-scrollbar-thumb { background: rgba(79,142,247,0.3); border-radius: 2px; }

.thumb {
  flex-shrink: 0; position: relative; cursor: pointer;
  border-radius: 7px; overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.2s;
}
.thumb:hover { transform: translateY(-3px); border-color: rgba(79,142,247,0.4); box-shadow: 0 6px 16px rgba(0,0,0,0.3); }
.thumb.active { border-color: #FFD700; box-shadow: 0 0 12px rgba(255,215,0,0.25); }
.thumb-img { width: 110px; height: 62px; object-fit: cover; display: block; }
.thumb-num {
  position: absolute; bottom: 3px; right: 4px;
  font-size: 9px; font-family: 'JetBrains Mono', monospace;
  color: rgba(255,255,255,0.7); background: rgba(0,0,0,0.5);
  padding: 1px 4px; border-radius: 3px;
}

.main-view {
  flex: 1; display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
.main-img {
  max-width: 100%; max-height: 100%; border-radius: 10px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(79,142,247,0.1);
  object-fit: contain;
}

.nav-bar {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; flex-shrink: 0;
}
.nav-btn {
  width: 32px; height: 32px; border-radius: 8px; border: none; cursor: pointer;
  background: rgba(79,142,247,0.1); border: 1px solid rgba(79,142,247,0.2);
  color: #4F8EF7; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.nav-btn:hover:not(:disabled) { background: rgba(79,142,247,0.2); box-shadow: 0 0 10px rgba(79,142,247,0.2); }
.nav-btn:disabled { opacity: 0.25; cursor: not-allowed; }

.page-counter { display: flex; align-items: baseline; gap: 4px; }
.page-cur { font-size: 18px; font-weight: 700; color: #4F8EF7; font-family: 'JetBrains Mono', monospace; }
.page-sep { font-size: 13px; color: rgba(226,232,248,0.25); }
.page-total { font-size: 13px; color: rgba(226,232,248,0.4); font-family: 'JetBrains Mono', monospace; }

.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.2s ease; }
.slide-fade-enter-from { opacity: 0; transform: scale(0.98); }
.slide-fade-leave-to { opacity: 0; transform: scale(1.01); }
</style>
