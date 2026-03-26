<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="chat-label">💬 意图对话</span>
      <span v-if="intentReady" class="done-badge">✓ 完成</span>
    </div>

    <div class="messages" ref="msgBox">
      <TransitionGroup name="msg">
        <div v-for="(m, i) in messages" :key="i" :class="['bubble-wrap', m.role]">
          <div class="avatar" :class="m.role">
            {{ m.role === 'user' ? '你' : 'AI' }}
          </div>
          <div class="bubble" :class="m.role" v-html="renderMd(m.content)"></div>
        </div>
      </TransitionGroup>

      <div v-if="loading" class="bubble-wrap assistant">
        <div class="avatar assistant">AI</div>
        <div class="bubble assistant typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <div class="input-row">
      <input
        v-model="input"
        class="chat-input"
        :placeholder="intentReady ? '意图收集完成' : '输入您的回答...' "
        :disabled="intentReady || loading"
        @keyup.enter="send"
      />
      <button class="send-btn" :disabled="!input.trim() || intentReady || loading" @click="send">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { sendChat } from '../api/index.js'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['intentReady'])
const messages = ref([])
const input = ref('')
const loading = ref(false)
const intentReady = ref(false)
const msgBox = ref(null)

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
  } finally {
    loading.value = false
  }
})

async function send() {
  const text = input.value.trim()
  if (!text) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  await scrollBottom()
  loading.value = true
  try {
    const data = await sendChat(messages.value)
    messages.value.push({ role: 'assistant', content: data.reply })
    if (data.intent_ready) {
      intentReady.value = true
      emit('intentReady', data.intent)
    }
  } catch (e) {
    ElMessage.error('对话请求失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
    await scrollBottom()
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex; flex-direction: column;
  background: rgba(10, 10, 30, 0.6);
  border: 1px solid rgba(79, 142, 247, 0.15);
  border-radius: 16px;
  overflow: hidden;
}

.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(79, 142, 247, 0.1);
  background: rgba(79, 142, 247, 0.05);
}
.chat-label { font-size: 12px; font-weight: 600; color: rgba(226, 232, 248, 0.6); letter-spacing: 0.5px; }
.done-badge {
  font-size: 10px; font-weight: 600; color: #4ade80;
  background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.3);
  padding: 2px 8px; border-radius: 99px;
}

.messages {
  flex: 1; overflow-y: auto;
  display: flex; flex-direction: column; gap: 12px;
  padding: 14px; min-height: 220px; max-height: 380px;
}

.bubble-wrap {
  display: flex; gap: 10px; align-items: flex-start;
}
.bubble-wrap.user { flex-direction: row-reverse; }

.avatar {
  width: 28px; height: 28px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
}
.avatar.assistant {
  background: linear-gradient(135deg, #4F8EF7, #7C3AED);
  color: white; box-shadow: 0 0 12px rgba(79, 142, 247, 0.3);
}
.avatar.user {
  background: rgba(255, 215, 0, 0.15);
  color: #FFD700; border: 1px solid rgba(255, 215, 0, 0.3);
}

.bubble {
  max-width: 82%; padding: 10px 14px; border-radius: 12px;
  font-size: 13.5px; line-height: 1.65; word-break: break-word;
  backdrop-filter: blur(12px);
}
.bubble.assistant {
  background: rgba(79, 142, 247, 0.08);
  border: 1px solid rgba(79, 142, 247, 0.2);
  border-left: 3px solid #4F8EF7;
  color: #d4dcf5;
  border-radius: 4px 12px 12px 12px;
}
.bubble.user {
  background: rgba(255, 215, 0, 0.08);
  border: 1px solid rgba(255, 215, 0, 0.2);
  color: #f0e8c0;
  border-radius: 12px 4px 12px 12px;
}

.typing {
  display: flex; gap: 5px; align-items: center; padding: 14px 16px;
}
.typing span {
  width: 7px; height: 7px; border-radius: 50%;
  background: linear-gradient(135deg, #4F8EF7, #7C3AED);
  animation: bounce 1.3s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-6px); opacity: 1; }
}

.input-row {
  display: flex; gap: 8px; padding: 12px 14px;
  border-top: 1px solid rgba(79, 142, 247, 0.1);
  background: rgba(8, 8, 24, 0.4);
}
.chat-input {
  flex: 1; background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(79, 142, 247, 0.2);
  border-radius: 10px; padding: 9px 14px;
  color: #e2e8f8; font-size: 13px; outline: none;
  font-family: inherit; transition: border-color 0.2s, box-shadow 0.2s;
}
.chat-input:focus {
  border-color: rgba(79, 142, 247, 0.5);
  box-shadow: 0 0 0 3px rgba(79, 142, 247, 0.08);
}
.chat-input:disabled { opacity: 0.4; cursor: not-allowed; }
.chat-input::placeholder { color: rgba(226, 232, 248, 0.25); }

.send-btn {
  width: 38px; height: 38px; border-radius: 10px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #4F8EF7, #7C3AED);
  color: white; display: flex; align-items: center; justify-content: center;
  transition: opacity 0.2s, box-shadow 0.2s, transform 0.15s;
  flex-shrink: 0;
}
.send-btn:hover:not(:disabled) {
  box-shadow: 0 0 16px rgba(79, 142, 247, 0.5);
  transform: translateY(-1px);
}
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.msg-enter-active { transition: all 0.3s ease; }
.msg-enter-from { opacity: 0; transform: translateY(8px); }
</style>
