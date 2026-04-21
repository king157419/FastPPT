<template>
  <div class="chat-panel">
    <div class="panel-header">
      <div class="panel-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke="#0D9488" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>备课对话</span>
      </div>
      <div class="panel-actions">
        <label class="agent-toggle" :class="{ disabled: messages.length > 1 || loading }">
          <input
            type="checkbox"
            v-model="useAgent"
            :disabled="messages.length > 1 || loading"
          />
          Agent
        </label>
        <span v-if="intentReady" class="done-badge">✓ 完成</span>
      </div>
    </div>

    <div class="messages" ref="msgBox">
      <TransitionGroup name="msg">
        <div v-for="(m, i) in messages" :key="i" :class="['msg-row', m.role]">
          <div class="avatar" :class="m.role">
            {{ m.role === 'user' ? '你' : 'AI' }}
          </div>
          <div class="bubble-wrap">
            <div class="bubble" :class="m.role" v-html="renderMd(m.content)"></div>
            <div v-if="m.tools?.length" class="tool-trace">
              <span v-for="(t, tIdx) in m.tools" :key="`${i}-${tIdx}`" class="tool-chip">
                🔧 {{ t }}
              </span>
            </div>
            <div v-if="m.toolTimeline?.length" class="tool-timeline">
              <div v-for="item in m.toolTimeline" :key="item.id" class="tool-timeline-item">
                <span class="tl-name">🔧 {{ item.name }}</span>
                <span class="tl-status" :class="item.status">{{ statusText(item.status) }}</span>
              </div>
            </div>
          </div>
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
        ref="chatInputEl"
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
import { ref, nextTick, onMounted, watch } from 'vue'
import { sendChat, sendChatStream, uploadAudio } from '../api/index.js'
import { ElMessage } from 'element-plus'

const props = defineProps({
  prefillPayload: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['intentReady'])
const messages = ref([])
const input = ref('')
const loading = ref(false)
const intentReady = ref(false)
const msgBox = ref(null)
const chatInputEl = ref(null)
const recording = ref(false)
const useAgent = ref(true)
const sessionId = ref('')
let mediaRecorder = null
let audioChunks = []

function renderMd(text) {
  return String(text || '')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

async function scrollBottom() {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

watch(
  () => props.prefillPayload,
  async (payload) => {
    if (!payload?.text) return
    const text = String(payload.text).trim()
    if (!text) return

    input.value = input.value ? `${input.value}\n${text}` : text
    await nextTick()
    chatInputEl.value?.focus()
  },
  { deep: true },
)

onMounted(async () => {
  await bootstrap()
})

async function bootstrap() {
  loading.value = true
  try {
    const data = await sendChat([], { useAgent: useAgent.value, sessionId: sessionId.value })
    if (data.session_id) sessionId.value = data.session_id
    messages.value.push({
      role: 'assistant',
      content: data.reply || '你好！请告诉我您想备什么课？',
      tools: [],
    })
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '你好！请告诉我您想备什么课？',
      tools: [],
    })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

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

function collectToolCalls(text, toolSet) {
  if (!text) return
  const patterns = [
    /Action\s*:\s*([A-Za-z_][\w]*)/gi,
    /Tool\s*:\s*([A-Za-z_][\w]*)/gi,
    /\[TOOL[:：]\s*([^\]]+)\]/gi,
    /工具(?:调用)?[:：]\s*([^\n]+)/gi,
  ]
  for (const pattern of patterns) {
    let match
    while ((match = pattern.exec(text)) !== null) {
      const name = String(match[1] || '').trim()
      if (name) toolSet.add(name)
    }
  }
}

function parseToolLifecycle(text) {
  const starts = []
  if (!text) return { starts, observations: 0, hasError: false }

  const actionPatterns = [
    /Action\s*:\s*([A-Za-z_][\w]*)/gi,
    /Tool\s*:\s*([A-Za-z_][\w]*)/gi,
    /\[TOOL[:：]\s*([^\]]+)\]/gi,
    /工具(?:调用)?[:：]\s*([^\n]+)/gi,
  ]
  for (const pattern of actionPatterns) {
    let match
    while ((match = pattern.exec(text)) !== null) {
      const name = normalizeToolName(match[1])
      if (name) starts.push(name)
    }
  }

  const observations = (text.match(/Observation\s*:|工具结果[:：]|返回结果[:：]/gi) || []).length
  const hasError = /tool[_\s-]*error|工具失败|调用失败/i.test(text)
  return { starts, observations, hasError }
}

function statusText(status) {
  if (status === 'running') return '执行中'
  if (status === 'done') return '已完成'
  if (status === 'error') return '失败'
  return status || '未知'
}

function normalizeToolName(name) {
  return String(name || '').trim().replace(/\s+/g, '_')
}

function ensureTimeline(message) {
  if (!Array.isArray(message.toolTimeline)) {
    message.toolTimeline = []
  }
}

function startTool(message, rawName) {
  const name = normalizeToolName(rawName)
  if (!name) return
  ensureTimeline(message)

  const running = message.toolTimeline.find((item) => item.name === name && item.status === 'running')
  if (running) return

  message.toolTimeline.push({
    id: `${name}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name,
    status: 'running',
  })
}

function finishTool(message, rawName, status = 'done') {
  ensureTimeline(message)
  const name = normalizeToolName(rawName)

  if (name) {
    const target = [...message.toolTimeline]
      .reverse()
      .find((item) => item.name === name && item.status === 'running')
    if (target) {
      target.status = status
      return
    }
  }

  const fallback = [...message.toolTimeline].reverse().find((item) => item.status === 'running')
  if (fallback) fallback.status = status
}

async function send() {
  const text = input.value.trim()
  if (!text || intentReady.value || loading.value) return
  messages.value.push({ role: 'user', content: text, tools: [] })
  input.value = ''
  await scrollBottom()

  const history = messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => ({ role: m.role, content: m.content }))

  const assistantMsg = { role: 'assistant', content: '', tools: [], toolTimeline: [] }
  messages.value.push(assistantMsg)
  await scrollBottom()

  loading.value = true
  const toolSet = new Set()
  let queue = ''
  let timer = null

  const updateToolTrace = () => {
    assistantMsg.tools = Array.from(toolSet)
  }

  const enqueue = async (chunk) => {
    if (!chunk) return
    collectToolCalls(chunk, toolSet)
    const lifecycle = parseToolLifecycle(chunk)
    lifecycle.starts.forEach((name) => startTool(assistantMsg, name))
    if (lifecycle.observations > 0) {
      for (let i = 0; i < lifecycle.observations; i += 1) {
        finishTool(assistantMsg, '')
      }
    }
    if (lifecycle.hasError) {
      finishTool(assistantMsg, '', 'error')
    }
    updateToolTrace()
    queue += chunk
    if (timer) return
    timer = setInterval(async () => {
      if (!queue.length) {
        clearInterval(timer)
        timer = null
        return
      }
      const step = queue.slice(0, 2)
      queue = queue.slice(2)
      assistantMsg.content += step
      await scrollBottom()
    }, 12)
  }

  const flush = async () => {
    if (queue.length) {
      assistantMsg.content += queue
      queue = ''
    }
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    await scrollBottom()
  }

  try {
    await sendChatStream(history, {
      useAgent: useAgent.value,
      sessionId: sessionId.value,
      onEvent: async (event) => {
        if (event.error) throw new Error(event.error)

        if (event.session_id) sessionId.value = event.session_id

        if (event.tool) {
          toolSet.add(event.tool)
          if (event.tool_status === 'done' || event.tool_status === 'success') {
            finishTool(assistantMsg, event.tool, 'done')
          } else if (event.tool_status === 'error' || event.tool_status === 'failed') {
            finishTool(assistantMsg, event.tool, 'error')
          } else {
            startTool(assistantMsg, event.tool)
          }
          updateToolTrace()
        }
        if (event.tool_call?.name) {
          toolSet.add(event.tool_call.name)
          const status = String(event.tool_call.status || '').toLowerCase()
          if (status.includes('error') || status.includes('fail')) {
            finishTool(assistantMsg, event.tool_call.name, 'error')
          } else if (status.includes('done') || status.includes('finish') || status.includes('success')) {
            finishTool(assistantMsg, event.tool_call.name, 'done')
          } else {
            startTool(assistantMsg, event.tool_call.name)
          }
          updateToolTrace()
        }
        if (event.chunk) await enqueue(event.chunk)

        if (event.done) {
          await flush()
          assistantMsg.toolTimeline
            .filter((item) => item.status === 'running')
            .forEach((item) => { item.status = 'done' })
          if (event.summary) assistantMsg.content = event.summary

          if (event.intent_ready) {
            intentReady.value = true
            emit('intentReady', event.intent)
          }
        }
      },
    })
  } catch (e) {
    await flush()
    assistantMsg.toolTimeline
      .filter((item) => item.status === 'running')
      .forEach((item) => { item.status = 'error' })
    assistantMsg.content = assistantMsg.content || `发送失败：${e.message}`
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
.panel-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.agent-toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--text-2);
  background: #f3f4f6;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 2px 8px;
}
.agent-toggle input {
  margin: 0;
}
.agent-toggle.disabled {
  opacity: 0.5;
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
.bubble-wrap {
  max-width: 78%;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.avatar {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.avatar.assistant { background: var(--teal-light); color: var(--teal); }
.avatar.user { background: #1C1C1E; color: white; }
.bubble {
  padding: 9px 13px;
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
.tool-trace {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.tool-chip {
  font-size: 10px;
  background: #e6fffa;
  color: #0f766e;
  border: 1px solid #99f6e4;
  border-radius: 999px;
  padding: 2px 7px;
}
.tool-timeline {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.tool-timeline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fafafa;
  padding: 4px 8px;
}
.tl-name {
  font-size: 11px;
  color: var(--text-2);
}
.tl-status {
  font-size: 10px;
  border-radius: 999px;
  padding: 1px 7px;
  border: 1px solid transparent;
}
.tl-status.running {
  color: #92400e;
  background: #fef3c7;
  border-color: #fcd34d;
}
.tl-status.done {
  color: #166534;
  background: #dcfce7;
  border-color: #86efac;
}
.tl-status.error {
  color: #991b1b;
  background: #fee2e2;
  border-color: #fca5a5;
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

@media (max-width: 768px) {
  .chat-panel {
    min-height: 260px;
    max-height: none;
  }
  .bubble-wrap {
    max-width: 86%;
  }
}
</style>
