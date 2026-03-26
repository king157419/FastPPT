<template>
  <div class="chat-panel">
    <div class="panel-header">
      <div class="panel-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="#0D9488" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>备课对话</span>
      </div>
      <span v-if="intentReady" class="done-badge">✓ 完成</span>
    </div>

    <div class="messages" ref="msgBox">
      <TransitionGroup name="msg">
        <div v-for="(m, i) in messages" :key="i" :class="['msg-row', m.role]">
          <div class="avatar" :class="m.role">
            {{ m.role === 'user' ? '你' : 'AI' }}
          </div>
          <div class="bubble" :class="m.role" v-html="renderMd(m.content)"></div>
        </div>
      </TransitionGroup>

      <div v-if="loading" class="msg-row assistant">
        <div class="avatar assistant">AI</div>
        <div class="bubble assistant typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <div class="input-row">
      <button class="mic-btn" :class="{ active: recording }" :disabled="intentReady" @click="toggleVoice" :title="recording ? '点击停止录音' : '语音输入'">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
          <rect x="9" y="2" width="6" height="12" rx="3" :fill="recording ? '#EF4444' : 'currentColor'"/>
          <path d="M5 10a7 7 0 0014 0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
      <input
        v-model="input"
        class="chat-input"
        :placeholder="intentReady ? '意图收集完成' : recording ? '录音中，点击麦克风停止...' : '描述您的备课需求...'"
        :disabled="intentReady || loading"
        @keyup.enter="send"
      />
      <button class="send-btn" :disabled="!input.trim() || intentReady || loading" @click="send">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <path d="M22 2L11 13" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { sendChat, uploadAudio } from '../api/index.js'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['intentReady'])
const messages = ref([])
const input = ref('')
const loading = ref(false)
const intentReady = ref(false)
const msgBox = ref(null)
const recording = ref(false)
let mediaRecorder = null
let audioChunks = []

function renderMd(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

async function scrollBottom() {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await sendChat([])
    messages.value.push({ role: 'assistant', content: data.reply })
    await scrollBottom()
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '你好！请告诉我您想备什么课？' })
  } finally {
    loading.value = false
  }
})

async function toggleVoice() {
  if (recording.value) {
    mediaRecorder?.stop()
    recording.value = false
    return
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioChunks = []
    mediaRecorder = new MediaRecorder(stream)
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data) }
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop())
      const blob = new Blob(audioChunks, { type: 'audio/wav' })
      loading.value = true
      try {
        const data = await uploadAudio(blob)
        if (data.text) { input.value = data.text }
      } catch (e) {
        ElMessage.error('语音识别失败：' + (e.response?.data?.detail || e.message))
      } finally { loading.value = false }
    }
    mediaRecorder.start()
    recording.value = true
  } catch (e) {
    ElMessage.error('无法访问麦克风：' + e.message)
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || intentReady.value || loading.value) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  await scrollBottom()
  loading.value = true
  try {
    const history = messages.value.map(m => ({ role: m.role, content: m.content }))
    const data = await sendChat(history)
    messages.value.push({ role: 'assistant', content: data.reply })
    if (data.intent_ready) {
      intentReady.value = true
      emit('intentReady', data.intent)
    }
  } catch (e) {
    ElMessage.error('发送失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
    await scrollBottom()
  }
}
</script>

<style scoped>
.chat-panel {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  display: flex; flex-direction: column;
  min-height: 280px; max-height: 380px;
  overflow: hidden;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.panel-title {
  display: flex; align-items: center; gap: 7px;
  font-size: 13px; font-weight: 600; color: var(--text);
}
.done-badge {
  font-size: 11px; font-weight: 600;
  color: var(--teal); background: var(--teal-light);
  padding: 2px 9px; border-radius: 99px;
}
.messages {
  flex: 1; overflow-y: auto; padding: 12px 14px;
  display: flex; flex-direction: column; gap: 10px;
}
.messages::-webkit-scrollbar { width: 3px; }
.messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.msg-row {
  display: flex; align-items: flex-end; gap: 8px;
}
.msg-row.user { flex-direction: row-reverse; }
.avatar {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.avatar.assistant { background: var(--teal-light); color: var(--teal); }
.avatar.user { background: #1C1C1E; color: white; }
.bubble {
  max-width: 78%; padding: 9px 13px;
  border-radius: 16px; font-size: 13px; line-height: 1.55;
}
.bubble.assistant {
  background: #F3F4F6; color: var(--text);
  border-bottom-left-radius: 4px;
}
.bubble.user {
  background: var(--teal); color: white;
  border-bottom-right-radius: 4px;
}
.bubble.typing {
  display: flex; align-items: center; gap: 4px;
  padding: 12px 16px;
}
.bubble.typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-3);
  animation: bounce 1.2s infinite;
}
.bubble.typing span:nth-child(2) { animation-delay: 0.2s; }
.bubble.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-5px); }
}
.input-row {
  display: flex; gap: 8px; padding: 10px 12px;
  border-top: 1px solid var(--border); flex-shrink: 0;
}
.chat-input {
  flex: 1; height: 38px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0 12px; font-size: 13px;
  font-family: inherit; color: var(--text);
  background: var(--bg); outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.chat-input:focus {
  border-color: var(--teal);
  box-shadow: 0 0 0 3px rgba(13,148,136,0.1);
}
.chat-input:disabled { opacity: 0.5; cursor: not-allowed; }
.chat-input::placeholder { color: var(--text-3); }
.mic-btn {
  width: 34px; height: 34px; border-radius: var(--radius-sm);
  border: 1.5px solid var(--border); cursor: pointer;
  background: var(--bg); color: var(--text-2);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s; flex-shrink: 0;
}
.mic-btn:hover:not(:disabled) { border-color: var(--teal); color: var(--teal); }
.mic-btn.active { background: #FEF2F2; border-color: #EF4444; color: #EF4444; animation: pulse 1s ease-in-out infinite; }
.mic-btn:disabled { opacity: 0.35; cursor: not-allowed; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.send-btn {
  width: 38px; height: 38px; border-radius: var(--radius-sm);
  border: none; cursor: pointer;
  background: var(--teal); color: white;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s, transform 0.15s;
  flex-shrink: 0;
}
.send-btn:hover:not(:disabled) { background: #0F766E; transform: translateY(-1px); }
.send-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.msg-enter-active { transition: all 0.25s ease; }
.msg-enter-from { opacity: 0; transform: translateY(6px); }
</style>
