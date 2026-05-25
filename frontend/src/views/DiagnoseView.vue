<template>
  <div v-if="!store.studentId" class="card">
    <p class="hint">请先在 ① 创建学生画像。</p>
    <button @click="$router.push('/profile')">返回画像</button>
  </div>

  <template v-else>
    <div class="card">
      <h2>② 模拟答卷</h2>
      <p class="hint">从题库随机抽 N 题(每题取自不同知识点)。逐题点击「对 / 错」,模拟学生的答题结果。</p>
      <div class="row">
        <span>
          <label>抽题数</label>
          <input type="number" v-model.number="n" min="1" max="10" style="width: 70px" />
        </span>
        <button class="secondary" :disabled="loading" @click="onSample">
          {{ store.questions.length ? '重新抽题' : '从题库抽题' }}
        </button>
        <span v-if="loading" class="status warn">加载中...</span>
        <span v-if="loadErr" class="status bad">{{ loadErr }}</span>
      </div>
    </div>

    <div v-if="store.questions.length" class="card">
      <h3>请逐题标记你「答对 / 答错」</h3>
      <div ref="questionsEl">
        <div v-for="(item, idx) in store.questions" :key="item.q.id" class="question">
          <div class="meta">
            Q{{ idx + 1 }} · [{{ item.q.concept_code }}] · 难度 {{ item.q.difficulty }} · 答案 {{ item.q.answer || '(主观)' }}
          </div>
          <div class="stem" v-html="item.q.stem"></div>
          <div class="choices">
            <span v-for="(v, k) in item.q.choices" :key="k" class="choice"><b>{{ k }}.</b> {{ v }}</span>
          </div>
          <div class="answer-mark">
            我答得:
            <button
              class="ans-btn secondary"
              :class="{ selected: item.answer === 'right', right: item.answer === 'right' }"
              @click="item.answer = 'right'"
            >✓ 对</button>
            <button
              class="ans-btn secondary"
              :class="{ selected: item.answer === 'wrong', wrong: item.answer === 'wrong' }"
              @click="item.answer = 'wrong'"
            >✗ 错</button>
          </div>
        </div>
      </div>

      <div class="row" style="margin-top: 14px">
        <button :disabled="diagnosing || !canSubmit" @click="onSubmit">
          {{ diagnosing ? '诊断中(LLM 调用约 5–15s)...' : '提交诊断' }}
        </button>
        <span v-if="!canSubmit" class="hint">至少标记 1 道题</span>
        <span v-if="diagStatus.text" :class="['status', diagStatus.kind]">{{ diagStatus.text }}</span>
      </div>
    </div>
  </template>
</template>

<script setup>
import { computed, nextTick, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { store } from '../store'
import { renderKatex } from '../utils/katex'

const router = useRouter()
const n = ref(5)
const loading = ref(false)
const loadErr = ref('')
const diagnosing = ref(false)
const diagStatus = reactive({ text: '', kind: 'ok' })
const questionsEl = ref(null)

const canSubmit = computed(() =>
  store.questions.some((it) => it.answer !== null && it.answer !== undefined),
)

async function onSample() {
  loading.value = true
  loadErr.value = ''
  try {
    const list = await api.sampleQuestions(n.value)
    store.questions = list.map((q) => ({ q, answer: null }))
    await nextTick()
    renderKatex(questionsEl.value)
  } catch (e) {
    loadErr.value = '✗ ' + e.message
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  diagnosing.value = true
  diagStatus.text = '调用 diagnose Agent (LLM)...'
  diagStatus.kind = 'warn'
  const answered = store.questions.filter((it) => it.answer !== null && it.answer !== undefined)
  const answers = answered.map((it) => ({
    question_id: it.q.id,
    concept_id: it.q.concept_code,
    correct: it.answer === 'right',
    seconds: 60,
  }))
  try {
    const res = await api.diagnose({
      student_id: store.studentId,
      answers,
    })
    store.diagnoseResult = res
    diagStatus.text = res.mock ? '⚠️ mock 兜底' : '✓ LLM 已调用'
    diagStatus.kind = res.mock ? 'warn' : 'ok'
    setTimeout(() => router.push('/path'), 600)
  } catch (e) {
    diagStatus.text = '✗ ' + e.message
    diagStatus.kind = 'bad'
  } finally {
    diagnosing.value = false
  }
}
</script>
