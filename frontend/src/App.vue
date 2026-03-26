<template>
  <div class="app-shell">
    <!-- 背景网格装饰 -->
    <div class="bg-grid"></div>
    <div class="bg-glow"></div>

    <!-- 顶部品牌栏 -->
    <header class="app-header">
      <div class="header-inner">
        <div class="brand">
          <span class="brand-icon">⚡</span>
          <span class="brand-name">TeachMind</span>
          <span class="brand-badge">AI</span>
        </div>
        <div class="brand-tagline">智能备课 · 一键生成课件</div>
        <div class="header-status">
          <span class="status-dot" :class="{ active: intentReady }"></span>
          <span class="status-text">{{ intentReady ? '意图就绪' : '等待对话' }}</span>
        </div>
      </div>
    </header>

    <!-- 主体两栏 -->
    <main class="app-body">
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
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; }
body {
  background: #080818;
  color: #e2e8f8;
  font-family: 'Sora', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a5a; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #4F8EF7; }

.app-shell {
  display: flex; flex-direction: column; height: 100vh;
  position: relative; overflow: hidden;
}

.bg-grid {
  position: fixed; inset: 0; z-index: 0;
  background-image:
    linear-gradient(rgba(79, 142, 247, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(79, 142, 247, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}
.bg-glow {
  position: fixed; top: -200px; left: 50%; transform: translateX(-50%);
  width: 800px; height: 400px; z-index: 0;
  background: radial-gradient(ellipse, rgba(79, 142, 247, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.app-header {
  flex-shrink: 0; z-index: 10;
  background: linear-gradient(135deg, rgba(79, 142, 247, 0.15), rgba(124, 58, 237, 0.12));
  border-bottom: 1px solid rgba(79, 142, 247, 0.2);
  backdrop-filter: blur(20px);
}
.header-inner {
  display: flex; align-items: center; gap: 16px;
  padding: 10px 24px;
}
.brand { display: flex; align-items: center; gap: 8px; }
.brand-icon { font-size: 20px; }
.brand-name {
  font-size: 18px; font-weight: 700; letter-spacing: -0.5px;
  background: linear-gradient(135deg, #4F8EF7, #FFD700);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.brand-badge {
  font-size: 10px; font-weight: 600; letter-spacing: 1px;
  background: linear-gradient(135deg, #4F8EF7, #7C3AED);
  color: white; padding: 2px 7px; border-radius: 99px;
  -webkit-text-fill-color: white;
}
.brand-tagline { font-size: 12px; color: rgba(226, 232, 248, 0.4); margin-left: 4px; }
.header-status { margin-left: auto; display: flex; align-items: center; gap: 6px; }
.status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #334; transition: background 0.4s;
}
.status-dot.active { background: #4ade80; box-shadow: 0 0 8px #4ade80; animation: pulse-green 2s infinite; }
@keyframes pulse-green {
  0%, 100% { box-shadow: 0 0 8px #4ade80; }
  50% { box-shadow: 0 0 16px #4ade80; }
}
.status-text { font-size: 11px; color: rgba(226, 232, 248, 0.5); font-family: 'JetBrains Mono', monospace; }

.app-body {
  display: flex; flex: 1; overflow: hidden; gap: 0;
  position: relative; z-index: 1;
}

.left-panel {
  width: 460px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 12px;
  overflow-y: auto; padding: 16px;
  border-right: 1px solid rgba(79, 142, 247, 0.1);
}

.right-panel {
  flex: 1; overflow: hidden; padding: 16px;
}
</style>
