<template>
  <div class="slide" :style="slideStyle">
    <!-- COVER -->
    <template v-if="page.type === 'cover'">
      <div class="cover-bar" :style="{ background: theme.accent }"></div>
      <div class="cover-body">
        <div class="cover-eyebrow" :style="{ color: theme.accent }">课件</div>
        <div class="cover-title" :style="{ color: theme.text }">{{ page.title }}</div>
        <div class="cover-sub" :style="{ color: theme.accent, opacity: 0.8 }">{{ page.subtitle }}</div>
      </div>
      <div class="cover-deco" :style="{ background: theme.accent }"></div>
    </template>

    <!-- AGENDA -->
    <template v-else-if="page.type === 'agenda'">
      <div class="s-header">
        <div class="s-label" :style="{ color: theme.accent }">目录</div>
        <div class="s-title" :style="{ color: theme.text }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="agenda-list">
        <div v-for="(item, i) in page.items" :key="i" class="agenda-item">
          <span class="a-num" :style="{ color: theme.accent }">{{ String(i+1).padStart(2,'0') }}</span>
          <span class="a-text" :style="{ color: theme.text }">{{ item }}</span>
        </div>
      </div>
    </template>

    <!-- CONTENT -->
    <template v-else-if="page.type === 'content'">
      <div class="s-header">
        <div class="s-title" :style="{ color: theme.accent }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="bullets">
        <div v-for="(b, i) in page.bullets" :key="i" class="bullet-item">
          <span class="b-dot" :style="{ background: theme.accent }"></span>
          <span class="b-text" :style="{ color: theme.text }">{{ b }}</span>
        </div>
      </div>
      <div v-if="page.tip" class="tip-bar">
        <span class="tip-icon">💡</span>
        <span class="tip-text" :style="{ color: theme.accent }">{{ page.tip }}</span>
      </div>
    </template>

    <!-- QUOTE -->
    <template v-else-if="page.type === 'quote'">
      <div class="quote-body">
        <div class="quote-mark" :style="{ color: theme.accent }">&ldquo;</div>
        <div class="quote-text" :style="{ color: theme.text }">{{ page.text }}</div>
        <div class="quote-mark quote-close" :style="{ color: theme.accent }">&rdquo;</div>
      </div>
    </template>

    <!-- CODE -->
    <template v-else-if="page.type === 'code'">
      <div class="s-header">
        <div class="s-title" :style="{ color: theme.accent }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="code-wrap">
        <div class="code-lang" :style="{ color: theme.accent }">{{ page.language }}</div>
        <pre class="code-block"><code v-html="highlightCode(page.code, page.language)"></code></pre>
        <div v-if="page.explanation" class="code-explain" :style="{ color: theme.text, opacity: 0.75 }">{{ page.explanation }}</div>
      </div>
    </template>

    <!-- FORMULA -->
    <template v-else-if="page.type === 'formula'">
      <div class="s-header">
        <div class="s-title" :style="{ color: theme.accent }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="formula-list">
        <div v-for="(f, i) in page.formulas" :key="i" class="formula-row" :style="{ borderLeftColor: theme.accent }">
          <span class="formula-label" :style="{ color: theme.accent }">{{ f.label }}</span>
          <span class="formula-expr" :style="{ color: theme.text }" v-html="renderKatex(f.expr)"></span>
        </div>
        <div v-if="page.explanation" class="formula-explain" :style="{ color: theme.text, opacity: 0.7 }">{{ page.explanation }}</div>
      </div>
    </template>

    <!-- EXAMPLE -->
    <template v-else-if="page.type === 'example'">
      <div class="s-header">
        <div class="s-title" :style="{ color: theme.accent }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="example-body">
        <div class="ex-problem" :style="{ color: theme.text, borderColor: theme.accent }">{{ page.problem }}</div>
        <div class="ex-steps">
          <div v-for="(s, i) in page.steps" :key="i" class="ex-step">
            <span class="step-num" :style="{ background: theme.accent, color: theme.primary }">{{ i + 1 }}</span>
            <span :style="{ color: theme.text }">{{ s }}</span>
          </div>
        </div>
        <div v-if="page.answer" class="ex-answer" :style="{ color: theme.accent }">
          <span class="answer-check">✓</span> {{ page.answer }}
        </div>
      </div>
    </template>

    <!-- TWO COLUMN -->
    <template v-else-if="page.type === 'two_column'">
      <div class="s-header">
        <div class="s-title" :style="{ color: theme.accent }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="two-cols">
        <div class="col">
          <div class="col-heading" :style="{ color: theme.accent }">{{ page.left?.heading }}</div>
          <div v-for="(p, i) in page.left?.points" :key="i" class="col-point" :style="{ color: theme.text }">
            <span class="col-dot" :style="{ background: theme.accent }"></span>{{ p }}
          </div>
        </div>
        <div class="col-divider" :style="{ background: theme.accent }"></div>
        <div class="col">
          <div class="col-heading" :style="{ color: theme.accent }">{{ page.right?.heading }}</div>
          <div v-for="(p, i) in page.right?.points" :key="i" class="col-point" :style="{ color: theme.text }">
            <span class="col-dot" :style="{ background: theme.accent }"></span>{{ p }}
          </div>
        </div>
      </div>
    </template>

    <!-- ANIMATION -->
    <template v-else-if="page.type === 'animation'">
      <div class="s-header">
        <div class="s-title" :style="{ color: theme.accent }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="anim-wrap">
        <iframe v-if="animSrc" :src="animSrc" class="anim-frame" frameborder="0" allowtransparency="true" scrolling="no"></iframe>
        <div v-else class="anim-placeholder" :style="{ color: theme.accent }">互动动画</div>
      </div>
    </template>

    <!-- IMAGE -->
    <template v-else-if="page.type === 'image'">
      <div class="s-header">
        <div class="s-title" :style="{ color: theme.accent }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="img-outer">
        <img v-if="page.image_base64" class="slide-img" :src="'data:image/jpeg;base64,' + page.image_base64" />
        <img v-else-if="page.image_url" class="slide-img" :src="page.image_url" />
        <div v-if="page.caption" class="img-caption" :style="{ color: theme.text, borderColor: theme.accent }">{{ page.caption }}</div>
      </div>
    </template>

    <!-- SUMMARY -->
    <template v-else-if="page.type === 'summary'">
      <div class="s-header">
        <div class="s-label" :style="{ color: theme.accent }">总结</div>
        <div class="s-title" :style="{ color: theme.text }">{{ page.title }}</div>
        <div class="s-line" :style="{ background: theme.accent }"></div>
      </div>
      <div class="bullets">
        <div v-for="(t, i) in page.takeaways" :key="i" class="bullet-item">
          <span class="b-check" :style="{ color: theme.accent }">✓</span>
          <span class="b-text" :style="{ color: theme.text }">{{ t }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import hljs from 'highlight.js/lib/core'
import python from 'highlight.js/lib/languages/python'
import javascript from 'highlight.js/lib/languages/javascript'
import cpp from 'highlight.js/lib/languages/cpp'
import java from 'highlight.js/lib/languages/java'
import c from 'highlight.js/lib/languages/c'
import 'highlight.js/styles/atom-one-dark.css'

hljs.registerLanguage('python', python)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('java', java)
hljs.registerLanguage('c', c)

function renderKatex(expr) {
  try {
    return katex.renderToString(expr, { throwOnError: false, displayMode: false })
  } catch {
    return expr
  }
}

function highlightCode(code, lang) {
  if (!code) return ''
  try {
    const l = lang?.toLowerCase()
    if (l && hljs.getLanguage(l)) {
      return hljs.highlight(code, { language: l }).value
    }
    return hljs.highlightAuto(code).value
  } catch {
    return code
  }
}

const props = defineProps({
  page: { type: Object, required: true },
  theme: { type: Object, required: true },
  mini: { type: Boolean, default: false }
})

const TEMPLATE_MAP = {
  bar_chart: '/templates/bar_chart.html',
  card_flip: '/templates/card_flip.html',
  flowchart: '/templates/flowchart.html',
  quiz: '/templates/quiz.html',
  timeline: '/templates/timeline.html',
}

const animSrc = computed(() => {
  if (props.page.type !== 'animation') return null
  const tpl = props.page.template
  const base = TEMPLATE_MAP[tpl]
  if (!base) return null
  const tdata = props.page.template_data
  if (tdata) {
    const hash = encodeURIComponent(JSON.stringify(tdata))
    return `${base}#${hash}`
  }
  return base
})
const slideStyle = computed(() => ({
  background: props.theme.primary,
  width: '100%', height: '100%',
  position: 'relative', overflow: 'hidden',
  fontFamily: '"Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif',
  fontSize: props.mini ? '28%' : '100%',
}))
</script>

<style scoped>
.slide { box-sizing: border-box; }

/* COVER */
.cover-bar { position: absolute; top: 0; left: 0; right: 0; height: 0.45em; }
.cover-body {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.6em; padding: 2em 3em; text-align: center;
}
.cover-eyebrow { font-size: 0.85em; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; opacity: 0.7; }
.cover-title { font-size: 3em; font-weight: 700; line-height: 1.2; }
.cover-sub { font-size: 1.2em; }
.cover-deco {
  position: absolute; bottom: -3em; right: -3em;
  width: 10em; height: 10em; border-radius: 50%; opacity: 0.07;
}

/* SHARED HEADER */
.s-header { position: absolute; top: 0.6em; left: 1em; right: 1em; }
.s-label { font-size: 0.7em; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; opacity: 0.7; margin-bottom: 0.2em; }
.s-title { font-size: 1.9em; font-weight: 700; line-height: 1.2; margin-bottom: 0.35em; }
.s-line { height: 0.18em; border-radius: 1px; width: 3em; }

/* AGENDA */
.agenda-list { position: absolute; top: 3.2em; left: 1.4em; right: 1em; display: flex; flex-direction: column; gap: 0.55em; }
.agenda-item { display: flex; align-items: center; gap: 0.75em; }
.a-num { font-size: 1.1em; font-weight: 700; font-family: monospace; min-width: 1.8em; opacity: 0.9; }
.a-text { font-size: 1.3em; line-height: 1.4; }

/* CONTENT */
.bullets { position: absolute; top: 3.4em; left: 1.2em; right: 1em; display: flex; flex-direction: column; gap: 0.65em; }
.bullet-item { display: flex; align-items: flex-start; gap: 0.6em; }
.b-dot { flex-shrink: 0; width: 0.42em; height: 0.42em; border-radius: 50%; margin-top: 0.5em; }
.b-check { font-size: 1.1em; font-weight: 700; flex-shrink: 0; min-width: 1.2em; }
.b-text { font-size: 1.3em; line-height: 1.45; }
.tip-bar {
  position: absolute; bottom: 0.7em; left: 1em; right: 1em;
  display: flex; align-items: center; gap: 0.4em;
  font-size: 0.85em; opacity: 0.85;
  padding: 0.4em 0.8em;
  background: rgba(255,255,255,0.06); border-radius: 0.4em;
}
.tip-icon { font-size: 1em; }
.tip-text { font-style: italic; }

/* CODE */
.code-wrap { position: absolute; top: 3.2em; left: 1em; right: 1em; bottom: 0.6em; display: flex; flex-direction: column; gap: 0.4em; }
.code-lang { font-size: 0.65em; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.8; }
.code-block {
  flex: 1; background: rgba(0,0,0,0.4); border-radius: 0.4em;
  padding: 0.7em 0.9em; margin: 0; overflow: hidden;
  font-family: 'Courier New', Consolas, monospace; font-size: 0.75em;
  line-height: 1.5; color: #e2e8f0; white-space: pre-wrap; word-break: break-all;
}
.code-explain { font-size: 0.78em; opacity: 0.75; font-style: italic; padding: 0 0.2em; }

/* FORMULA */
.formula-list { position: absolute; top: 3.2em; left: 1.2em; right: 1em; display: flex; flex-direction: column; gap: 0.7em; }
.formula-row {
  display: flex; align-items: baseline; gap: 0.8em;
  border-left: 0.2em solid; padding-left: 0.6em;
}
.formula-label { font-size: 0.78em; font-weight: 700; min-width: 6em; opacity: 0.9; }
.formula-expr { font-size: 1.5em; font-family: Georgia, 'Times New Roman', serif; font-style: italic; line-height: 1.3; }
.formula-explain { font-size: 0.8em; opacity: 0.65; font-style: italic; margin-top: 0.4em; padding-left: 0.6em; }

/* EXAMPLE */
.example-body { position: absolute; top: 3.2em; left: 1.2em; right: 1em; bottom: 0.6em; display: flex; flex-direction: column; gap: 0.55em; }
.ex-problem {
  font-size: 0.95em; line-height: 1.4; padding: 0.5em 0.8em;
  border-left: 0.22em solid; border-radius: 0 0.3em 0.3em 0;
  background: rgba(255,255,255,0.06);
}
.ex-steps { display: flex; flex-direction: column; gap: 0.35em; }
.ex-step { display: flex; align-items: flex-start; gap: 0.5em; font-size: 0.85em; line-height: 1.4; }
.step-num {
  flex-shrink: 0; width: 1.3em; height: 1.3em; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75em; font-weight: 700; margin-top: 0.1em;
}
.ex-answer { font-size: 0.95em; font-weight: 700; display: flex; align-items: center; gap: 0.4em; margin-top: 0.2em; }
.answer-check { font-size: 1.1em; }

/* TWO COLUMN */
.two-cols { position: absolute; top: 3.2em; left: 1em; right: 1em; bottom: 0.6em; display: flex; gap: 0; }
.col { flex: 1; display: flex; flex-direction: column; gap: 0.45em; padding: 0 0.6em; }
.col-divider { width: 0.12em; align-self: stretch; opacity: 0.4; margin: 0 0.3em; }
.col-heading { font-size: 0.9em; font-weight: 700; margin-bottom: 0.2em; letter-spacing: 0.03em; }
.col-point { display: flex; align-items: flex-start; gap: 0.4em; font-size: 0.8em; line-height: 1.4; }
.col-dot { flex-shrink: 0; width: 0.35em; height: 0.35em; border-radius: 50%; margin-top: 0.45em; }

/* ANIMATION */
.anim-wrap { position: absolute; top: 3.2em; left: 1em; right: 1em; bottom: 0.6em; }
.anim-frame { width: 100%; height: 100%; border-radius: 0.4em; background: transparent; }
.anim-placeholder { display: flex; align-items: center; justify-content: center; height: 100%; font-size: 1.2em; opacity: 0.4; }

/* IMAGE */
.img-outer { position: absolute; top: 3.2em; left: 1em; right: 1em; bottom: 0.6em; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.4em; }
.slide-img { max-width: 100%; max-height: 85%; object-fit: contain; border-radius: 0.4em; }
.img-caption { font-size: 0.8em; font-style: italic; opacity: 0.8; text-align: center; border-left: 0.2em solid; padding-left: 0.5em; }

/* QUOTE */
.quote-body {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 2em 2.5em; gap: 0.3em;
}
.quote-mark { font-size: 4em; font-family: Georgia, serif; line-height: 0.8; opacity: 0.5; }
.quote-close { align-self: flex-end; }
.quote-text { font-size: 1.8em; text-align: center; line-height: 1.5; font-style: italic; }
</style>
