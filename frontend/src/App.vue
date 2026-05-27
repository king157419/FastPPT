<template>
  <div class="app-shell">
    <div class="ambient ambient-a"></div>
    <div class="ambient ambient-b"></div>
    <header class="app-header">
      <div class="header-inner">
        <div class="brand">
          <div class="brand-logo">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="8" height="8" rx="2" fill="#0D9488"/>
              <rect x="13" y="3" width="8" height="8" rx="2" fill="#0D9488" opacity="0.5"/>
              <rect x="3" y="13" width="8" height="8" rx="2" fill="#0D9488" opacity="0.5"/>
              <rect x="13" y="13" width="8" height="8" rx="2" fill="#0D9488"/>
            </svg>
          </div>
          <div class="brand-copy">
            <span class="brand-name">FastPPT Studio</span>
            <span class="brand-sub">Contest Demo</span>
          </div>
        </div>
        <div class="header-center">
          <span class="tagline">AI 智能备课助手</span>
        </div>
        <div class="header-status">
          <div class="status-pill" :class="{ ready: intentReady }">
            <span class="status-dot"></span>
            <span>{{ intentReady ? '准备生成' : '对话中' }}</span>
          </div>
        </div>
      </div>
    </header>

    <main class="app-body">
      <aside class="left-panel">
        <FileUpload @uploaded="onUploaded" />
        <DocumentPanel @insertPrompt="onInsertPrompt" />
        <RequirementForm @intentReady="onIntentReady" />
        <ChatPanel
          :prefillPayload="chatPrefill"
          @intentReady="onIntentReady"
        />
        <GenerateBtn
          :intentReady="intentReady"
          :intent="intent"
          :fileIds="fileIds"
          @generated="onGenerated"
        />
      </aside>
      <section class="right-panel">
        <div class="preview-shell">
          <PreviewPanel
            :slidesJson="slidesJson"
            :generatedResult="generatedResult"
            @slidesUpdated="onSlidesUpdated"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import DocumentPanel from './components/DocumentPanel.vue'
import RequirementForm from './components/RequirementForm.vue'
import ChatPanel from './components/ChatPanel.vue'
import GenerateBtn from './components/GenerateBtn.vue'
import PreviewPanel from './components/PreviewPanel.vue'

const intentReady = ref(false)
const intent = ref(null)
const fileIds = ref([])
const slidesJson = ref(null)
const generatedResult = ref(null)
const chatPrefill = ref(null)

function onUploaded({ fileId }) { fileIds.value.push(fileId) }
function onIntentReady(data) { intentReady.value = true; intent.value = data }
function onGenerated(data) {
  generatedResult.value = data || null
  slidesJson.value = data?.slides_json || null
}
function onSlidesUpdated(nextSlides) {
  slidesJson.value = nextSlides
  if (generatedResult.value) {
    generatedResult.value = { ...generatedResult.value, slides_json: nextSlides }
  }
}
function onInsertPrompt(text) {
  chatPrefill.value = { text, nonce: Date.now() }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Sans:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'DM Sans', sans-serif;
  background: #e9f1ec;
  color: #102520;
  -webkit-font-smoothing: antialiased;
}

:root {
  --teal: #0f766e;
  --teal-light: #cffafe;
  --teal-mid: #14b8a6;
  --bg: #edf4ef;
  --surface: rgba(255, 255, 255, 0.84);
  --surface-strong: #ffffff;
  --border: #d6e4dd;
  --text: #102520;
  --text-2: #506760;
  --text-3: #7e958d;
  --shadow-sm: 0 2px 8px rgba(9, 29, 22, 0.06);
  --shadow-md: 0 10px 28px rgba(9, 29, 22, 0.1);
  --shadow-lg: 0 22px 48px rgba(9, 29, 22, 0.16);
  --radius: 16px;
  --radius-sm: 8px;
}

.app-shell {
  display: flex; flex-direction: column;
  height: 100vh; overflow: hidden;
  background:
    radial-gradient(circle at 8% -10%, rgba(20, 184, 166, 0.22), transparent 42%),
    radial-gradient(circle at 100% 0%, rgba(245, 158, 11, 0.18), transparent 35%),
    linear-gradient(160deg, #eef5f0 0%, #e4f0ea 55%, #f5f6ef 100%);
  position: relative;
}

.ambient {
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
  filter: blur(40px);
  opacity: 0.35;
  z-index: 0;
}

.ambient-a {
  width: 320px;
  height: 320px;
  background: rgba(20, 184, 166, 0.4);
  top: -130px;
  left: -80px;
}

.ambient-b {
  width: 280px;
  height: 280px;
  background: rgba(245, 158, 11, 0.3);
  bottom: -100px;
  right: 15%;
}

.app-header {
  height: 64px; flex-shrink: 0;
  background: rgba(255, 255, 255, 0.64);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  z-index: 10;
  position: relative;
}
.header-inner {
  max-width: 100%; height: 100%;
  display: flex; align-items: center;
  padding: 0 24px; gap: 16px;
}
.brand { display: flex; align-items: center; gap: 10px; }
.brand-logo {
  width: 40px; height: 40px;
  background: linear-gradient(145deg, #c2faf6, #f9fffd);
  border: 1px solid rgba(15, 118, 110, 0.2);
  border-radius: 12px; display: flex; align-items: center; justify-content: center;
}
.brand-copy {
  display: flex;
  flex-direction: column;
  line-height: 1.05;
}
.brand-name {
  font-family: 'Outfit', sans-serif;
  font-size: 18px; font-weight: 700;
  color: var(--text); letter-spacing: -0.3px;
}
.brand-sub {
  font-size: 11px;
  color: var(--text-3);
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.header-center { flex: 1; display: flex; justify-content: center; }
.tagline {
  font-size: 12px;
  color: var(--text-2);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.header-status { margin-left: auto; }
.status-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 99px;
  font-size: 12px; font-weight: 500;
  background: #F3F4F6; color: var(--text-2);
  transition: all 0.3s;
}
.status-pill.ready { background: var(--teal-light); color: var(--teal); }
.status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-3); transition: background 0.3s;
}
.status-pill.ready .status-dot {
  background: var(--teal);
  box-shadow: 0 0 6px var(--teal);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; } 50% { opacity: 0.5; }
}

.app-body {
  display: flex; flex: 1; overflow: hidden;
  gap: 12px;
  padding: 12px;
  position: relative;
  z-index: 1;
}
.left-panel {
  width: 430px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 10px;
  overflow-y: auto; padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.48);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(6px);
}
.left-panel::-webkit-scrollbar { width: 4px; }
.left-panel::-webkit-scrollbar-thumb { background: rgba(80, 103, 96, 0.35); border-radius: 2px; }
.right-panel {
  flex: 1; overflow: hidden;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.48);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(6px);
  min-width: 0;
}
.preview-shell {
  width: 100%;
  height: 100%;
  padding: 14px;
}
.left-panel > * {
  animation: enter-up 420ms ease both;
}
.left-panel > *:nth-child(2) { animation-delay: 50ms; }
.left-panel > *:nth-child(3) { animation-delay: 90ms; }
.left-panel > *:nth-child(4) { animation-delay: 130ms; }

@keyframes enter-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 980px) {
  .app-body {
    flex-direction: column;
    padding: 8px;
    gap: 8px;
  }
  .left-panel {
    width: 100%;
    border-bottom: none;
    max-height: 46vh;
    padding: 10px;
  }
  .right-panel {
    min-height: 54vh;
  }
  .preview-shell {
    padding: 8px;
  }
  .header-inner {
    padding: 0 12px;
  }
  .tagline {
    display: none;
  }
}
</style>
