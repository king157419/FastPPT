<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="logo">🎓 TeachMind</div>
      <div class="tagline">AI 智能备课系统</div>
    </header>

    <main class="app-body">
      <!-- 左栏 -->
      <aside class="left-panel">
        <FileUpload @uploaded="onUploaded" />
        <ChatPanel @intentReady="onIntentReady" />
        <GenerateBtn
          :intentReady="intentReady"
          :intent="intent"
          :fileIds="fileIds"
          @generated="onGenerated"
        />
      </aside>

      <!-- 右栏 -->
      <section class="right-panel">
        <PreviewPanel :pptxFilename="pptxFilename" />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FileUpload from './components/FileUpload.vue'
import ChatPanel from './components/ChatPanel.vue'
import GenerateBtn from './components/GenerateBtn.vue'
import PreviewPanel from './components/PreviewPanel.vue'

const intentReady = ref(false)
const intent = ref(null)
const fileIds = ref([])
const pptxFilename = ref('')

function onUploaded({ fileId }) {
  fileIds.value.push(fileId)
}

function onIntentReady(data) {
  intentReady.value = true
  intent.value = data
}

function onGenerated(data) {
  pptxFilename.value = data.pptx
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; }
body { background: #0a0a1a; color: #e0e0f0; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }

.app-shell { display: flex; flex-direction: column; height: 100vh; }

.app-header {
  display: flex; align-items: center; gap: 16px;
  padding: 12px 24px;
  background: #111122;
  border-bottom: 1px solid #2a2a4e;
  flex-shrink: 0;
}
.logo { font-size: 20px; font-weight: 700; color: #ffd700; }
.tagline { font-size: 13px; color: #909399; }

.app-body {
  display: flex; flex: 1; overflow: hidden; gap: 16px;
  padding: 16px;
}

.left-panel {
  width: 420px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 12px;
  overflow-y: auto;
}

.right-panel {
  flex: 1; overflow: hidden;
}
</style>
