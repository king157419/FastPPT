<template>
  <div class="preview-panel">
    <div class="panel-header">
      <div class="panel-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="#0D9488" stroke-width="2" />
          <path d="M8 21h8M12 17v4" stroke="#0D9488" stroke-width="2" stroke-linecap="round" />
        </svg>
        <span>课件预览</span>
      </div>
      <div class="header-actions">
        <span v-if="pages.length" class="slide-count">{{ pages.length }} 页</span>
        <button v-if="pages.length" class="outline-btn" @click="showBlocks = !showBlocks">
          {{ showBlocks ? "隐藏 Block" : "显示 Block" }}
        </button>
        <a
          v-if="backendPptxUrl"
          class="export-btn backend"
          :href="backendPptxUrl"
          :download="backendPptxFilename"
        >
          下载后端 PPTX
        </a>
        <button v-if="pages.length" class="export-btn" @click="exportPPTX">导出本地 .pptx</button>
      </div>
    </div>

    <div v-if="!pages.length" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <rect x="2" y="3" width="20" height="14" rx="2" stroke="#D1D5DB" stroke-width="1.5" />
          <path d="M8 21h8M12 17v4" stroke="#D1D5DB" stroke-width="1.5" stroke-linecap="round" />
        </svg>
      </div>
      <div class="empty-title">暂无预览</div>
      <div class="empty-sub">完成对话并生成课件后，幻灯片将显示在此处。</div>
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
            <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
        <span class="page-counter">
          <span class="page-cur">{{ currentIndex + 1 }}</span>
          <span class="page-sep">/</span>
          <span class="page-total">{{ pages.length }}</span>
        </span>
        <button class="nav-btn" :disabled="currentIndex >= pages.length - 1" @click="currentIndex++">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <div class="revise-panel">
        <input
          v-model="reviseText"
          class="revise-input"
          :disabled="revising"
          placeholder="输入修改要求，例如：第2页增加课堂互动问题"
          @keyup.enter="handleRevise"
        />
        <label class="revise-toggle">
          <input v-model="onlyCurrentPage" type="checkbox" :disabled="revising" />
          仅修改当前页
        </label>
        <button class="revise-btn" :disabled="!reviseText.trim() || revising" @click="handleRevise">
          {{ revising ? "修改中..." : "修改 PPT" }}
        </button>
      </div>

      <div class="evidence-panel">
        <div class="evidence-header">
          <span>来源证据（第 {{ currentIndex + 1 }} 页）</span>
          <button class="outline-btn" @click="showEvidence = !showEvidence">
            {{ showEvidence ? "收起" : "展开" }}
          </button>
        </div>
        <div v-if="showEvidence">
          <div v-if="!currentEvidence.length" class="evidence-empty">当前页暂无来源证据。</div>
          <div v-else class="evidence-list">
            <div v-for="(item, idx) in currentEvidence" :key="idx" class="evidence-item">
              <div class="evidence-meta">{{ evidenceLabel(item) }}</div>
              <div class="evidence-snippet">{{ item.snippet }}</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showBlocks" class="block-panel">
        <div class="block-header">
          <span>Block 视图（第 {{ currentIndex + 1 }} 页）</span>
          <span v-if="blockSummary" class="block-meta">总块数 {{ blockSummary.total_blocks || 0 }}</span>
        </div>
        <div v-if="!currentBlocks.length" class="block-empty">当前页暂无 block 数据</div>
        <div v-else class="block-list">
          <div v-for="block in currentBlocks" :key="block.id || block.type" class="block-item">
            <div class="block-top">
              <span class="block-type">{{ block.type }}</span>
              <span class="block-id">{{ block.id }}</span>
            </div>
            <div class="block-preview">{{ payloadPreview(block.payload) }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { ElMessage } from "element-plus"
import pptxgen from "pptxgenjs"

import { downloadUrl, modifyCourse, normalizeGenerateResult } from "../api/index.js"
import SlideRenderer from "./SlideRenderer.vue"

const props = defineProps({
  slidesJson: { type: Object, default: null },
  generatedResult: { type: Object, default: null },
})

const emit = defineEmits(["slidesUpdated"])

const currentIndex = ref(0)
const showBlocks = ref(true)
const showEvidence = ref(true)
const reviseText = ref("")
const revising = ref(false)
const onlyCurrentPage = ref(true)
const latestPptxFilename = ref("")

const theme = computed(
  () => props.slidesJson?.theme || { primary: "#0f172a", accent: "#0D9488", text: "#f8fafc" },
)
const pages = computed(() => props.slidesJson?.pages || [])
const currentPage = computed(() => pages.value[currentIndex.value] || {})
const currentBlocks = computed(() => currentPage.value?.blocks || [])
const currentEvidence = computed(() =>
  Array.isArray(currentPage.value?.evidence) ? currentPage.value.evidence : [],
)
const blockSummary = computed(() => props.slidesJson?.meta?.block_summary || null)
const normalizedResult = computed(() => normalizeGenerateResult(props.generatedResult || {}))
const backendPptxFilename = computed(() => latestPptxFilename.value || normalizedResult.value.pptx || "")
const backendPptxUrl = computed(() =>
  backendPptxFilename.value ? downloadUrl(backendPptxFilename.value) : "",
)

watch(
  () => props.slidesJson,
  () => {
    currentIndex.value = 0
  },
)

watch(
  () => props.generatedResult,
  () => {
    latestPptxFilename.value = ""
  },
)

function payloadPreview(payload) {
  if (!payload) return ""
  try {
    return JSON.stringify(payload).slice(0, 160)
  } catch {
    return String(payload).slice(0, 160)
  }
}

function evidenceLabel(item) {
  const fileName = item?.file_name || "unknown"
  const where = item?.page_or_slide || "unknown"
  const score = Number(item?.score || 0).toFixed(2)
  return `${fileName} | ${where} | score ${score}`
}

function textBlockByRole(blocks, role) {
  const item = blocks.find((block) => block?.type === "TextBlock" && block?.payload?.role === role)
  return item?.payload?.text || ""
}

function firstBlock(blocks, type) {
  return blocks.find((block) => block?.type === type)
}

function toTextArray(value) {
  if (!Array.isArray(value)) return []
  return value.map((item) => String(item)).filter(Boolean)
}

function exportBlocksPage(slide, page, blocks, t, hex) {
  const title = textBlockByRole(blocks, "title") || page.title || ""
  const subtitle = textBlockByRole(blocks, "subtitle") || page.subtitle || ""
  const hasHeroSlot = blocks.some((b) => b?.layoutHints?.slot === "hero")

  if (page.type === "cover" || hasHeroSlot) {
    slide.addShape(pptxgen.ShapeType.rect, {
      x: 0,
      y: 0,
      w: 13.33,
      h: 0.1,
      fill: { color: hex(t.accent) },
      line: { color: hex(t.accent) },
    })
    slide.addText(title, {
      x: 0.5,
      y: 2.0,
      w: 12.3,
      h: 1.4,
      fontSize: 40,
      bold: true,
      color: hex(t.text),
      align: "center",
      fontFace: "Microsoft YaHei",
    })
    slide.addText(subtitle, {
      x: 0.5,
      y: 3.6,
      w: 12.3,
      h: 0.7,
      fontSize: 20,
      color: hex(t.accent),
      align: "center",
      fontFace: "Microsoft YaHei",
    })
    return
  }

  slide.addText(title, {
    x: 0.7,
    y: 0.35,
    w: 11.9,
    h: 0.75,
    fontSize: 26,
    bold: true,
    color: hex(t.accent),
    fontFace: "Microsoft YaHei",
  })
  slide.addShape(pptxgen.ShapeType.rect, {
    x: 0.7,
    y: 1.15,
    w: 11.6,
    h: 0.04,
    fill: { color: hex(t.accent) },
    line: { color: hex(t.accent) },
  })

  let y = 1.4
  const tipText = textBlockByRole(blocks, "teaching_tip")

  const bullet = firstBlock(blocks, "BulletBlock")
  if (bullet) {
    const items = toTextArray(bullet?.payload?.items)
    const bulletData = items.map((item) => ({
      text: item,
      options: {
        fontSize: 18,
        color: hex(t.text),
        bullet: { type: "number" },
        fontFace: "Microsoft YaHei",
        paraSpaceAfter: 10,
      },
    }))
    if (bulletData.length) {
      slide.addText(bulletData, { x: 0.9, y, w: 11.2, h: 3.8 })
      y += 3.9
    }
  }

  const code = firstBlock(blocks, "CodeBlock")
  if (code) {
    const payload = code.payload || {}
    slide.addText((payload.language || "").toUpperCase(), {
      x: 0.7,
      y,
      w: 2.0,
      h: 0.3,
      fontSize: 10,
      bold: true,
      color: hex(t.accent),
      fontFace: "Courier New",
    })
    slide.addShape(pptxgen.ShapeType.rect, {
      x: 0.5,
      y: y + 0.3,
      w: 12.3,
      h: 2.4,
      fill: { color: "1e293b" },
      line: { color: "1e293b" },
    })
    slide.addText(payload.code || "", {
      x: 0.7,
      y: y + 0.4,
      w: 11.9,
      h: 2.2,
      fontSize: 12,
      color: "e2e8f0",
      fontFace: "Courier New",
      valign: "top",
      wrap: true,
    })
    if (payload.explanation) {
      slide.addText(payload.explanation, {
        x: 0.7,
        y: y + 2.8,
        w: 11.9,
        h: 0.4,
        fontSize: 12,
        color: hex(t.text),
        italic: true,
        fontFace: "Microsoft YaHei",
      })
    }
    y += 3.3
  }

  const tip = tipText ? `提示：${tipText}` : ""
  if (tip) {
    slide.addText(tip, {
      x: 0.6,
      y: 6.6,
      w: 12.1,
      h: 0.35,
      fontSize: 11,
      color: "FFD700",
      italic: true,
      align: "right",
      fontFace: "Microsoft YaHei",
    })
  }
}

async function exportPPTX() {
  const pptx = new pptxgen()
  pptx.layout = "LAYOUT_WIDE"
  const t = theme.value
  const hex = (c) => c.replace("#", "")

  for (const page of pages.value) {
    const slide = pptx.addSlide()
    slide.background = { color: hex(t.primary) }
    const blocks = Array.isArray(page?.blocks) ? page.blocks : []

    if (blocks.length) {
      exportBlocksPage(slide, page, blocks, t, hex)
      continue
    }

    if (page.type === "cover") {
      slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: 13.33,
        h: 0.1,
        fill: { color: hex(t.accent) },
        line: { color: hex(t.accent) },
      })
      slide.addText(page.title || "", {
        x: 0.5,
        y: 2.0,
        w: 12.3,
        h: 1.4,
        fontSize: 40,
        bold: true,
        color: hex(t.text),
        align: "center",
        fontFace: "Microsoft YaHei",
      })
      slide.addText(page.subtitle || "", {
        x: 0.5,
        y: 3.6,
        w: 12.3,
        h: 0.7,
        fontSize: 20,
        color: hex(t.accent),
        align: "center",
        fontFace: "Microsoft YaHei",
      })
    } else if (page.type === "agenda") {
      slide.addText(page.title || "目录", {
        x: 0.7,
        y: 0.4,
        w: 11.9,
        h: 0.8,
        fontSize: 28,
        bold: true,
        color: hex(t.text),
        fontFace: "Microsoft YaHei",
      })
      const items = (page.items || []).map((item, i) => ({
        text: `${i + 1}. ${item}`,
        options: { fontSize: 20, color: hex(t.text), fontFace: "Microsoft YaHei", paraSpaceAfter: 10 },
      }))
      slide.addText(items, { x: 1.2, y: 1.5, w: 10, h: 5 })
    } else {
      slide.addText(page.title || "", {
        x: 0.7,
        y: 0.35,
        w: 11.9,
        h: 0.75,
        fontSize: 26,
        bold: true,
        color: hex(t.accent),
        fontFace: "Microsoft YaHei",
      })
      const bullets = (page.bullets || page.takeaways || []).map((b) => ({
        text: String(b),
        options: {
          fontSize: 18,
          color: hex(t.text),
          bullet: { type: "bullet" },
          fontFace: "Microsoft YaHei",
          paraSpaceAfter: 12,
        },
      }))
      if (bullets.length) {
        slide.addText(bullets, { x: 0.9, y: 1.4, w: 11.2, h: 4.8 })
      }
    }
  }
  await pptx.writeFile({ fileName: "课件.pptx" })
}

async function handleRevise() {
  const instruction = reviseText.value.trim()
  if (!instruction) {
    ElMessage.warning("请先输入修改要求")
    return
  }

  revising.value = true
  try {
    const page_indexes = onlyCurrentPage.value ? [currentIndex.value + 1] : []
    const payload = {
      intent: props.generatedResult?.teaching_spec || props.generatedResult?.intent || {},
      slides_json: props.slidesJson || {},
      instruction,
      page_indexes,
    }
    const res = await modifyCourse(payload)
    const normalized = normalizeGenerateResult(res || {})
    if (!normalized.slides_json) {
      throw new Error("后端未返回 slides_json")
    }
    emit("slidesUpdated", normalized.slides_json)
    if (normalized.pptx) latestPptxFilename.value = normalized.pptx
    reviseText.value = ""
    ElMessage.success(normalized.message || "课件修改已完成")
  } catch (err) {
    ElMessage.error(`课件修改失败：${err?.response?.data?.detail || err.message}`)
  } finally {
    revising.value = false
  }
}
</script>

<style scoped>
.preview-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 16px;
  overflow: hidden;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.slide-count {
  font-size: 11px;
  color: var(--teal);
  background: var(--teal-light);
  padding: 2px 9px;
  border-radius: 99px;
}
.outline-btn {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--text-2);
  border: 1px solid var(--border);
  cursor: pointer;
  font-weight: 600;
}
.outline-btn:hover {
  border-color: var(--teal);
  color: var(--teal);
}
.export-btn {
  font-size: 11px;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  background: var(--teal);
  color: #fff;
  border: none;
  cursor: pointer;
  font-weight: 600;
  text-decoration: none;
}
.export-btn.backend {
  background: #0f766e;
}
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-3);
}
.empty-icon {
  opacity: 0.5;
}
.empty-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-2);
}
.empty-sub {
  font-size: 12px;
  color: var(--text-3);
  text-align: center;
  max-width: 240px;
  line-height: 1.5;
}
.thumb-strip {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  flex-shrink: 0;
  padding-bottom: 4px;
}
.thumb {
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  border: 2px solid transparent;
  width: 110px;
  height: 62px;
  aspect-ratio: 16/9;
  background: #000;
}
.thumb.active {
  border-color: var(--teal);
  box-shadow: 0 0 0 2px var(--teal-light);
}
.thumb-inner {
  width: 100%;
  height: 100%;
}
.thumb-num {
  position: absolute;
  bottom: 3px;
  right: 4px;
  font-size: 9px;
  font-family: monospace;
  color: #fff;
  background: rgba(0, 0, 0, 0.45);
  padding: 1px 4px;
  border-radius: 3px;
  z-index: 2;
}
.main-view {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 12px;
  min-height: 0;
  container-type: size;
}
.main-slide {
  aspect-ratio: 16/9;
  width: min(100cqw, calc(100cqh * 16 / 9));
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  flex-shrink: 0;
}
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-shrink: 0;
}
.nav-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  cursor: pointer;
  background: var(--bg);
  color: var(--text-2);
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.page-counter {
  display: flex;
  align-items: baseline;
  gap: 3px;
}
.page-cur {
  font-size: 18px;
  font-weight: 700;
  color: var(--teal);
  font-family: monospace;
}
.page-sep,
.page-total {
  font-size: 13px;
  color: var(--text-3);
}
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.2s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: scale(0.99);
}
.slide-fade-leave-to {
  opacity: 0;
}
.revise-panel {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px;
}
.revise-input {
  flex: 1;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0 10px;
  font-size: 12px;
  outline: none;
}
.revise-input:focus {
  border-color: var(--teal);
}
.revise-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-2);
}
.revise-btn {
  height: 32px;
  border: none;
  border-radius: 8px;
  padding: 0 12px;
  background: var(--teal);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.revise-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.evidence-panel {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px;
}
.evidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
}
.evidence-empty {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-3);
}
.evidence-list {
  margin-top: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.evidence-item {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fafafa;
  padding: 6px 8px;
}
.evidence-meta {
  font-size: 11px;
  font-weight: 600;
  color: var(--teal);
}
.evidence-snippet {
  margin-top: 3px;
  font-size: 11px;
  color: var(--text-2);
  line-height: 1.45;
  word-break: break-word;
}
.block-panel {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 8px;
  max-height: 180px;
  overflow-y: auto;
}
.block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 7px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
}
.block-meta {
  color: var(--text-3);
}
.block-empty {
  font-size: 12px;
  color: var(--text-3);
}
.block-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.block-item {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 7px;
  background: #fafafa;
}
.block-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.block-type {
  font-size: 11px;
  font-weight: 700;
  color: var(--teal);
}
.block-id {
  font-size: 10px;
  color: var(--text-3);
  font-family: monospace;
}
.block-preview {
  font-size: 11px;
  color: var(--text-2);
  word-break: break-word;
}

@media (max-width: 768px) {
  .preview-panel {
    padding: 10px;
    gap: 8px;
  }
  .thumb {
    width: 84px;
    height: 48px;
  }
  .main-view {
    padding: 6px;
  }
  .nav-bar {
    gap: 10px;
  }
  .block-panel {
    max-height: 140px;
  }
}
</style>
