<template>
  <div class="app-shell">
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
          <span class="brand-name">TeachMind</span>
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
        <PreviewPanel
          :slidesJson="slidesJson"
          :generatedResult="generatedResult"
          @slidesUpdated="onSlidesUpdated"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import DocumentPanel from './components/DocumentPanel.vue'
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
  background: #F7F6F3;
  color: #1C1C1E;
  -webkit-font-smoothing: antialiased;
}

:root {
  --teal: #0D9488;
  --teal-light: #CCFBF1;
  --teal-mid: #14B8A6;
  --bg: #F7F6F3;
  --surface: #FFFFFF;
  --border: #E8E6E1;
  --text: #1C1C1E;
  --text-2: #6B7280;
  --text-3: #9CA3AF;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 12px 32px rgba(0,0,0,0.1), 0 4px 8px rgba(0,0,0,0.04);
  --radius: 12px;
  --radius-sm: 8px;
}

.app-shell {
  display: flex; flex-direction: column;
  height: 100vh; overflow: hidden;
  background: var(--bg);
}

.app-header {
  height: 56px; flex-shrink: 0;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  z-index: 10;
}
.header-inner {
  max-width: 100%; height: 100%;
  display: flex; align-items: center;
  padding: 0 24px; gap: 16px;
}
.brand { display: flex; align-items: center; gap: 10px; }
.brand-logo {
  width: 36px; height: 36px; background: var(--teal-light);
  border-radius: 10px; display: flex; align-items: center; justify-content: center;
}
.brand-name {
  font-family: 'Outfit', sans-serif;
  font-size: 18px; font-weight: 700;
  color: var(--text); letter-spacing: -0.3px;
}
.header-center { flex: 1; display: flex; justify-content: center; }
.tagline {
  font-size: 13px; color: var(--text-3);
  font-weight: 400; letter-spacing: 0.2px;
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
}
.left-panel {
  width: 420px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 10px;
  overflow-y: auto; padding: 16px;
  border-right: 1px solid var(--border);
  background: var(--bg);
}
.left-panel::-webkit-scrollbar { width: 4px; }
.left-panel::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.right-panel {
  flex: 1; overflow: hidden; padding: 16px;
  background: var(--bg);
}

@media (max-width: 980px) {
  .app-body {
    flex-direction: column;
  }
  .left-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border);
    max-height: 46vh;
  }
  .right-panel {
    min-height: 54vh;
    padding: 10px;
  }
  .header-inner {
    padding: 0 12px;
  }
  .tagline {
    display: none;
  }
}
</style>
