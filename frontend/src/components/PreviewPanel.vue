<template>
  <div class="preview-panel">
    <div class="panel-header">
      <div class="panel-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="#0D9488" stroke-width="2"/>
          <path d="M8 21h8M12 17v4" stroke="#0D9488" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>课件预览</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center">
        <span v-if="pages.length" class="slide-count">{{ pages.length }} 页</span>
        <button v-if="pages.length" class="export-btn" @click="exportPPTX">↓ 导出 .pptx</button>
      </div>
    </div>

    <div v-if="!pages.length" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="#D1D5DB" stroke-width="1.5"/>
          <path d="M8 21h8M12 17v4" stroke="#D1D5DB" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="empty-title">暂无预览</div>
      <div class="empty-sub">完成对话并生成课件后，幻灯片将显示在此处</div>
    </div>

    <template v-if="pages.length">
      <div class="thumb-strip">
        <div
          v-for="(page, i) in pages"
          :key="i"
          class="thumb"
          :class="{ active: currentIndex === i }"
          @click="currentIndex = i"
        >
          <div class="thumb-inner">
            <SlideRenderer :page="page" :theme="theme" :mini="true" />
          </div>
          <span class="thumb-num">{{ i + 1 }}</span>
        </div>
      </div>

      <div class="main-view">
        <Transition name="slide-fade" mode="out-in">
          <div :key="currentIndex" class="main-slide">
            <SlideRenderer :page="pages[currentIndex]" :theme="theme" :mini="false" />
          </div>
        </Transition>
      </div>

      <div class="nav-bar">
        <button class="nav-btn" :disabled="currentIndex <= 0" @click="currentIndex--">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <span class="page-counter">
          <span class="page-cur">{{ currentIndex + 1 }}</span>
          <span class="page-sep">/</span>
          <span class="page-total">{{ pages.length }}</span>
        </span>
        <button class="nav-btn" :disabled="currentIndex >= pages.length - 1" @click="currentIndex++">
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
import pptxgen from 'pptxgenjs'
import SlideRenderer from './SlideRenderer.vue'

const props = defineProps({ slidesJson: { type: Object, default: null } })
const currentIndex = ref(0)
const theme = computed(() => props.slidesJson?.theme || { primary: '#0f172a', accent: '#0D9488', text: '#f8fafc' })
const pages = computed(() => props.slidesJson?.pages || [])
watch(() => props.slidesJson, () => { currentIndex.value = 0 })

async function exportPPTX() {
  const pptx = new pptxgen()
  pptx.layout = 'LAYOUT_WIDE'
  const t = theme.value
  const hex = c => c.replace('#', '')

  for (const page of pages.value) {
    const slide = pptx.addSlide()
    slide.background = { color: hex(t.primary) }

    if (page.type === 'cover') {
      slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.1, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      slide.addText(page.title || '', { x: 0.5, y: 2.0, w: 12.3, h: 1.4, fontSize: 40, bold: true, color: hex(t.text), align: 'center', fontFace: 'Microsoft YaHei' })
      slide.addText(page.subtitle || '', { x: 0.5, y: 3.6, w: 12.3, h: 0.7, fontSize: 20, color: hex(t.accent), align: 'center', fontFace: 'Microsoft YaHei' })
    } else if (page.type === 'agenda') {
      slide.addText(page.title || '目录', { x: 0.7, y: 0.4, w: 11.9, h: 0.8, fontSize: 28, bold: true, color: hex(t.text), fontFace: 'Microsoft YaHei' })
      const items = (page.items || []).map((item, i) => ({ text: `${i + 1}.  ${item}`, options: { fontSize: 20, color: hex(t.text), fontFace: 'Microsoft YaHei', paraSpaceAfter: 10 } }))
      slide.addText(items, { x: 1.2, y: 1.5, w: 10, h: 5 })
    } else if (page.type === 'content') {
      slide.addText(page.title || '', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      const bullets = (page.bullets || []).map(b => ({ text: b, options: { fontSize: 18, color: hex(t.text), bullet: { type: 'number' }, fontFace: 'Microsoft YaHei', paraSpaceAfter: 12 } }))
      slide.addText(bullets, { x: 0.9, y: 1.4, w: 11.2, h: 4.5 })
      if (page.tip) slide.addText('💡 ' + page.tip, { x: 0.5, y: 6.6, w: 12.3, h: 0.5, fontSize: 12, color: 'FFD700', italic: true, fontFace: 'Microsoft YaHei', align: 'right' })
    } else if (page.type === 'code') {
      slide.addText(page.title || '', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      slide.addText((page.language || '').toUpperCase(), { x: 0.7, y: 1.25, w: 2, h: 0.3, fontSize: 10, bold: true, color: hex(t.accent), fontFace: 'Courier New' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.5, y: 1.6, w: 12.3, h: 4.0, fill: { color: '1e293b' }, line: { color: '1e293b' } })
      slide.addText(page.code || '', { x: 0.7, y: 1.7, w: 11.9, h: 3.8, fontSize: 13, color: 'e2e8f0', fontFace: 'Courier New', valign: 'top', wrap: true })
      if (page.explanation) slide.addText(page.explanation, { x: 0.7, y: 5.75, w: 11.9, h: 0.5, fontSize: 13, color: hex(t.text), italic: true, fontFace: 'Microsoft YaHei' })
    } else if (page.type === 'formula') {
      slide.addText(page.title || '', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      let fy = 1.5
      for (const f of (page.formulas || [])) {
        slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: fy, w: 0.06, h: 0.55, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
        slide.addText([{ text: (f.label || '') + ':  ', options: { bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' } }, { text: f.expr || '', options: { italic: true, color: hex(t.text), fontFace: 'Georgia' } }], { x: 0.9, y: fy, w: 11.4, h: 0.55, fontSize: 22 })
        fy += 0.75
      }
      if (page.explanation) slide.addText(page.explanation, { x: 0.9, y: fy + 0.2, w: 11.4, h: 0.6, fontSize: 14, color: hex(t.text), italic: true, fontFace: 'Microsoft YaHei' })
    } else if (page.type === 'example') {
      slide.addText(page.title || '', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      slide.addText('题目：' + (page.problem || ''), { x: 0.7, y: 1.3, w: 11.9, h: 0.8, fontSize: 17, color: hex(t.text), fontFace: 'Microsoft YaHei', bold: false })
      const steps = (page.steps || []).map((s, i) => ({ text: `Step ${i + 1}：${s}`, options: { fontSize: 15, color: hex(t.text), fontFace: 'Microsoft YaHei', paraSpaceAfter: 6 } }))
      if (steps.length) slide.addText(steps, { x: 0.7, y: 2.2, w: 11.9, h: 3.2 })
      if (page.answer) slide.addText('✓  ' + page.answer, { x: 0.7, y: 5.6, w: 11.9, h: 0.65, fontSize: 17, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
    } else if (page.type === 'two_column') {
      slide.addText(page.title || '', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      slide.addText(page.left?.heading || '', { x: 0.5, y: 1.3, w: 5.8, h: 0.55, fontSize: 18, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      const lpts = (page.left?.points || []).map(p => ({ text: '•  ' + p, options: { fontSize: 15, color: hex(t.text), fontFace: 'Microsoft YaHei', paraSpaceAfter: 8 } }))
      if (lpts.length) slide.addText(lpts, { x: 0.5, y: 2.0, w: 5.8, h: 4.5 })
      slide.addShape(pptx.ShapeType.rect, { x: 6.55, y: 1.25, w: 0.05, h: 5.0, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      slide.addText(page.right?.heading || '', { x: 6.85, y: 1.3, w: 5.8, h: 0.55, fontSize: 18, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      const rpts = (page.right?.points || []).map(p => ({ text: '•  ' + p, options: { fontSize: 15, color: hex(t.text), fontFace: 'Microsoft YaHei', paraSpaceAfter: 8 } }))
      if (rpts.length) slide.addText(rpts, { x: 6.85, y: 2.0, w: 5.8, h: 4.5 })
    } else if (page.type === 'animation') {
      slide.addText(page.title || '', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      slide.addText(`[互动动画: ${page.template || ''}]`, { x: 1.5, y: 2.5, w: 10.3, h: 2, fontSize: 18, color: hex(t.text), align: 'center', italic: true, fontFace: 'Microsoft YaHei' })
    } else if (page.type === 'image') {
      slide.addText(page.title || '', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.accent), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      if (page.image_base64) {
        slide.addImage({ data: 'data:image/jpeg;base64,' + page.image_base64, x: 1.5, y: 1.5, w: 10.3, h: 4.8, sizing: { type: 'contain', w: 10.3, h: 4.8 } })
      }
      if (page.caption) slide.addText(page.caption, { x: 0.7, y: 6.5, w: 11.9, h: 0.4, fontSize: 12, color: hex(t.text), italic: true, align: 'center', fontFace: 'Microsoft YaHei' })
    } else if (page.type === 'quote') {
      slide.addText(page.text || '', { x: 1, y: 2.5, w: 11.3, h: 2, fontSize: 28, color: hex(t.accent), align: 'center', italic: true, fontFace: 'Microsoft YaHei' })
    } else if (page.type === 'summary') {
      slide.addText(page.title || '课程总结', { x: 0.7, y: 0.35, w: 11.9, h: 0.75, fontSize: 26, bold: true, color: hex(t.text), fontFace: 'Microsoft YaHei' })
      slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: 1.15, w: 11.6, h: 0.04, fill: { color: hex(t.accent) }, line: { color: hex(t.accent) } })
      const items = (page.takeaways || []).map(tw => ({ text: '✓  ' + tw, options: { fontSize: 20, color: hex(t.accent), fontFace: 'Microsoft YaHei', paraSpaceAfter: 14 } }))
      slide.addText(items, { x: 1.2, y: 1.6, w: 10, h: 4.5 })
    }
  }
  await pptx.writeFile({ fileName: '课件.pptx' })
}
</script>

<style scoped>
.preview-panel {
  height: 100%; display: flex; flex-direction: column; gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 16px; overflow: hidden;
}
.panel-header {
  display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;
}
.panel-title {
  display: flex; align-items: center; gap: 7px;
  font-size: 13px; font-weight: 600; color: var(--text);
}
.slide-count {
  font-size: 11px; color: var(--teal);
  background: var(--teal-light); padding: 2px 9px; border-radius: 99px;
}
.export-btn {
  font-size: 11px; padding: 4px 12px; border-radius: var(--radius-sm);
  background: var(--teal); color: white; border: none;
  cursor: pointer; font-weight: 600; transition: background 0.2s;
}
.export-btn:hover { background: #0F766E; }
.empty-state {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; color: var(--text-3);
}
.empty-icon { opacity: 0.5; }
.empty-title { font-size: 15px; font-weight: 500; color: var(--text-2); }
.empty-sub { font-size: 12px; color: var(--text-3); text-align: center; max-width: 240px; line-height: 1.5; }
.thumb-strip {
  display: flex; gap: 8px; overflow-x: auto; flex-shrink: 0; padding-bottom: 4px;
}
.thumb-strip::-webkit-scrollbar { height: 3px; }
.thumb-strip::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.thumb {
  flex-shrink: 0; position: relative; cursor: pointer;
  border-radius: 6px; overflow: hidden;
  border: 2px solid transparent; transition: all 0.2s;
  width: 110px; height: 62px;
}
.thumb-inner { width: 100%; height: 100%; }
.thumb:hover { transform: translateY(-2px); border-color: var(--teal-mid); box-shadow: var(--shadow-md); }
.thumb.active { border-color: var(--teal); box-shadow: 0 0 0 2px var(--teal-light); }
.thumb-num {
  position: absolute; bottom: 3px; right: 4px;
  font-size: 9px; font-family: monospace;
  color: white; background: rgba(0,0,0,0.45);
  padding: 1px 4px; border-radius: 3px; z-index: 2;
}
.main-view {
  flex: 1; display: flex; align-items: center; justify-content: center; overflow: hidden;
}
.main-slide {
  width: 100%; height: 100%; border-radius: 10px; overflow: hidden;
  box-shadow: var(--shadow-lg);
}
.nav-bar {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; flex-shrink: 0;
}
.nav-btn {
  width: 32px; height: 32px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); cursor: pointer;
  background: var(--bg); color: var(--text-2);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.nav-btn:hover:not(:disabled) { border-color: var(--teal); color: var(--teal); background: var(--teal-light); }
.nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-counter { display: flex; align-items: baseline; gap: 3px; }
.page-cur { font-size: 18px; font-weight: 700; color: var(--teal); font-family: monospace; }
.page-sep { font-size: 13px; color: var(--text-3); }
.page-total { font-size: 13px; color: var(--text-3); font-family: monospace; }
.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.2s ease; }
.slide-fade-enter-from { opacity: 0; transform: scale(0.99); }
.slide-fade-leave-to { opacity: 0; }
</style>
