<template>
  <div class="chat-panel">
    <div class="chat-label">💬 多轮意图对话</div>
    <div class="messages" ref="msgBox">
      <div v-for="(m, i) in messages" :key="i" :class="['bubble', m.role]">
        <div class="avatar">{{ m.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="content" v-html="renderMd(m.content)"></div>
      </div>
      <div v-if="loading" class="bubble assistant">
        <div class="avatar">🤖</div>
        <div class="content typing"><span></span><span></span><span></span></div>
      </div>
    </div>
    <div class="input-row">
      <el-input
        v-model="input"
        :placeholder="intentReady ? '意图收集完成，可生成课件' : '输入您的回答...' "
        :disabled="intentReady || loading"
        @keyup.enter="send"
        size="large"
        clearable
      />
      <el-button
        type="primary"
        :disabled="!input.trim() || intentReady || loading"
        @click="send"
        size="large"
      >发送</el-button>
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
  // 触发第一个问题
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
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.chat-label { font-size: 13px; color: #909399; margin-bottom: 8px; font-weight: 500; }
.messages {
  flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;
  padding: 8px; background: #0d0d1a; border-radius: 8px; min-height: 200px; max-height: 360px;
}
.bubble { display: flex; gap: 8px; align-items: flex-start; }
.bubble.user { flex-direction: row-reverse; }
.avatar { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
.content {
  max-width: 80%; padding: 10px 14px; border-radius: 12px;
  font-size: 14px; line-height: 1.6; word-break: break-word;
}
.bubble.assistant .content { background: #1a1a2e; color: #e0e0f0; border-bottom-left-radius: 4px; }
.bubble.user .content { background: #0f3a7a; color: #ffffff; border-bottom-right-radius: 4px; }
.typing { display: flex; gap: 4px; align-items: center; padding: 14px; }
.typing span {
  width: 8px; height: 8px; border-radius: 50%; background: #5b8cf0;
  animation: bounce 1.2s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
.input-row { display: flex; gap: 8px; margin-top: 10px; }
.input-row .el-input { flex: 1; }
</style>
