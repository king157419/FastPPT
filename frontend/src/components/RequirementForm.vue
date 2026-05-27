<template>
  <div class="req-form">
    <div class="rf-head">
      <span class="rf-title">结构化需求</span>
      <span class="rf-sub">填表直接生成 · 或用下方对话澄清</span>
    </div>

    <div class="rf-grid">
      <label class="rf-field">
        <span>课程主题 *</span>
        <input v-model="topic" type="text" placeholder="如：高等数学 - 拉格朗日中值定理" />
      </label>
      <label class="rf-field">
        <span>教学目标 *</span>
        <textarea v-model="teachingGoal" rows="2" placeholder="如：理解定理条件与几何意义，并能用于证明" />
      </label>
      <div class="rf-row">
        <label class="rf-field">
          <span>面向学生 *</span>
          <input v-model="audience" type="text" placeholder="如：本科一年级" />
        </label>
        <label class="rf-field rf-narrow">
          <span>课时</span>
          <input v-model="duration" type="text" placeholder="45分钟" />
        </label>
      </div>
      <label class="rf-field">
        <span>重点难点 *</span>
        <input v-model="difficulty" type="text" placeholder="如：定理条件的理解与应用" />
      </label>
      <label class="rf-field">
        <span>知识点（每行一个，可选）</span>
        <textarea v-model="keyPointsText" rows="3" placeholder="中值定理表述与条件&#10;几何意义&#10;证明思路&#10;典型应用" />
      </label>
      <div class="rf-row">
        <label class="rf-field">
          <span>风格</span>
          <select v-model="style">
            <option>简洁学术</option>
            <option>理工公式密集</option>
            <option>案例驱动</option>
            <option>活泼通俗</option>
          </select>
        </label>
        <div class="rf-checks">
          <label><input type="checkbox" v-model="needImages" /> 配示意图</label>
          <label><input type="checkbox" v-model="needCases" /> 最新案例</label>
        </div>
      </div>
    </div>

    <div v-if="missing.length" class="rf-warn">还需填写：{{ missing.join('、') }}</div>
    <div v-else class="rf-summary">
      将生成《{{ topic }}》 · {{ audience }} · {{ duration }}<template v-if="keyPoints.length"> · {{ keyPoints.length }} 个知识点</template>
    </div>

    <button class="rf-btn" :class="{ ready: !missing.length }" :disabled="missing.length > 0" @click="confirm">
      {{ confirmed ? '需求已确认 · 可重新提交' : '确认需求并解锁生成' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['intentReady'])

const topic = ref('')
const teachingGoal = ref('')
const audience = ref('')
const duration = ref('45分钟')
const difficulty = ref('')
const keyPointsText = ref('')
const style = ref('简洁学术')
const needImages = ref(true)
const needCases = ref(true)
const confirmed = ref(false)

const keyPoints = computed(() =>
  keyPointsText.value
    .split(/[\n,，;；]/)
    .map((s) => s.trim())
    .filter(Boolean),
)

const missing = computed(() => {
  const m = []
  if (!topic.value.trim()) m.push('课程主题')
  if (!teachingGoal.value.trim()) m.push('教学目标')
  if (!audience.value.trim()) m.push('面向学生')
  if (!difficulty.value.trim()) m.push('重点难点')
  return m
})

function confirm() {
  if (missing.value.length) return
  confirmed.value = true
  emit('intentReady', {
    topic: topic.value.trim(),
    teaching_goal: teachingGoal.value.trim(),
    audience: audience.value.trim(),
    duration: duration.value.trim() || '45分钟',
    difficulty_focus: difficulty.value.trim(),
    style: style.value,
    key_points: keyPoints.value,
    need_images: needImages.value,
    need_latest_cases: needCases.value,
  })
}
</script>

<style scoped>
.req-form {
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: var(--surface, rgba(255, 255, 255, 0.84));
  backdrop-filter: blur(8px);
  border-radius: var(--radius, 16px);
  padding: 12px;
  box-shadow: var(--shadow-sm, 0 2px 8px rgba(9, 29, 22, 0.06));
}
.rf-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; }
.rf-title { font-size: 13px; font-weight: 700; color: var(--text, #102520); }
.rf-sub { font-size: 10px; color: var(--text-3, #7e958d); }
.rf-grid { display: flex; flex-direction: column; gap: 8px; }
.rf-row { display: flex; gap: 8px; }
.rf-row .rf-field { flex: 1; }
.rf-narrow { max-width: 40%; }
.rf-field { display: flex; flex-direction: column; gap: 4px; }
.rf-field span { font-size: 11px; color: var(--text-2, #506760); }
.rf-field input,
.rf-field textarea,
.rf-field select {
  border: 1px solid #bdd3cb;
  border-radius: var(--radius-sm, 8px);
  padding: 7px 9px;
  font-size: 12px;
  font-family: inherit;
  color: var(--text, #102520);
  outline: none;
  background: #fafafa;
  resize: vertical;
}
.rf-field input:focus,
.rf-field textarea:focus,
.rf-field select:focus {
  border-color: var(--teal, #0f766e);
  box-shadow: 0 0 0 2px rgba(13, 148, 136, 0.1);
  background: #fff;
}
.rf-checks { display: flex; flex-direction: column; justify-content: flex-end; gap: 4px; font-size: 11px; color: var(--text-2, #506760); }
.rf-checks label { display: flex; align-items: center; gap: 5px; cursor: pointer; }
.rf-warn {
  margin-top: 8px; font-size: 11px; color: #b45309;
  background: #fef3c7; border: 1px solid #fcd34d; border-radius: 8px; padding: 5px 8px;
}
.rf-summary { margin-top: 8px; font-size: 11px; color: var(--teal, #0f766e); font-weight: 600; }
.rf-btn {
  margin-top: 10px; width: 100%; height: 38px;
  border: none; border-radius: var(--radius-sm, 8px);
  cursor: pointer; font-size: 13px; font-weight: 600; font-family: inherit;
  background: #dce6e3; color: #6f7f79; transition: all 0.22s;
}
.rf-btn.ready {
  background: linear-gradient(130deg, #0f766e, #14b8a6);
  color: #fff; box-shadow: 0 8px 20px rgba(20, 184, 166, 0.28);
}
.rf-btn.ready:hover { transform: translateY(-1px); box-shadow: 0 12px 26px rgba(20, 184, 166, 0.36); }
.rf-btn:disabled { cursor: not-allowed; }
</style>
