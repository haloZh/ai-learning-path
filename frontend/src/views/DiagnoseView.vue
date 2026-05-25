<template>
  <template v-if="!store.studentId">
    <n-card>
      <n-empty description="请先在第 1 步创建学生画像">
        <template #extra>
          <n-button type="primary" @click="$router.push('/profile')">返回画像</n-button>
        </template>
      </n-empty>
    </n-card>
  </template>

  <template v-else>
    <n-card title="✏️ 模拟答卷">
      <template #header-extra>
        <n-tag round :bordered="false" type="warning">第 2 步</n-tag>
      </template>

      <n-text depth="3" style="font-size: 13px">
        从 {{ totalQuestions }} 道题库中随机抽 N 题(每题取自不同知识点),
        逐题点击「✓ 对 / ✗ 错」模拟学生答题。
      </n-text>

      <n-space align="center" style="margin: 14px 0 0">
        <span style="font-size: 13px; color: #666">抽题数</span>
        <n-input-number v-model:value="n" :min="1" :max="10" style="width: 110px" />
        <n-button :loading="loading" @click="onSample">
          🎲 {{ store.questions.length ? '重新抽题' : '从题库抽题' }}
        </n-button>
        <n-tag v-if="store.questions.length" :bordered="false">
          已抽 {{ store.questions.length }} 题
        </n-tag>
      </n-space>
    </n-card>

    <div v-if="store.questions.length" ref="questionsEl" style="margin-top: 14px">
      <div
        v-for="(item, idx) in store.questions"
        :key="item.q.id"
        :class="[
          'q-card',
          item.answer === 'right' && 'answered-right',
          item.answer === 'wrong' && 'answered-wrong',
        ]"
      >
        <div class="q-meta">
          <n-tag size="small" type="info" round>Q{{ idx + 1 }}</n-tag>
          <n-tag size="small" :bordered="false">{{ item.q.concept_code }}</n-tag>
          <n-tag size="small" :bordered="false" :type="diffType(item.q.difficulty)">
            难度 {{ item.q.difficulty }}
          </n-tag>
          <n-tag size="small" :bordered="false" type="success">
            标准答案 {{ item.q.answer || '(主观)' }}
          </n-tag>
        </div>
        <div class="q-stem" v-html="item.q.stem"></div>
        <div class="q-choices">
          <span v-for="(v, k) in item.q.choices" :key="k" class="q-choice">
            <b>{{ k }}.</b> {{ v }}
          </span>
        </div>
        <div class="q-actions">
          <span class="label">我答得:</span>
          <n-button
            size="small"
            :type="item.answer === 'right' ? 'success' : 'default'"
            :ghost="item.answer !== 'right'"
            @click="item.answer = 'right'"
          >✓ 对</n-button>
          <n-button
            size="small"
            :type="item.answer === 'wrong' ? 'error' : 'default'"
            :ghost="item.answer !== 'wrong'"
            @click="item.answer = 'wrong'"
          >✗ 错</n-button>
        </div>
      </div>

      <n-space justify="end" align="center" style="margin-top: 18px">
        <n-text depth="3" style="font-size: 13px">
          已标记 {{ answeredCount }} / {{ store.questions.length }}
        </n-text>
        <n-button
          type="primary"
          size="large"
          :loading="diagnosing"
          :disabled="!answeredCount"
          @click="onSubmit"
        >
          {{ diagnosing ? '诊断中(LLM 调用 5–15s)...' : '🩺 提交诊断' }}
        </n-button>
      </n-space>
    </div>
  </template>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { api } from '../api'
import { store } from '../store'
import { renderKatex } from '../utils/katex'

const router = useRouter()
const message = useMessage()
const n = ref(5)
const loading = ref(false)
const diagnosing = ref(false)
const questionsEl = ref(null)
const totalQuestions = ref(389)  // 仅展示用

const answeredCount = computed(() =>
  store.questions.filter((it) => it.answer !== null && it.answer !== undefined).length,
)

function diffType(d) {
  if (d <= 1) return 'success'
  if (d <= 3) return 'info'
  return 'error'
}

async function onSample() {
  loading.value = true
  try {
    const list = await api.sampleQuestions(n.value)
    store.questions = list.map((q) => ({ q, answer: null }))
    await nextTick()
    renderKatex(questionsEl.value)
  } catch (e) {
    message.error('抽题失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  diagnosing.value = true
  const answered = store.questions.filter((it) => it.answer !== null && it.answer !== undefined)
  const answers = answered.map((it) => ({
    question_id: it.q.id,
    concept_id: it.q.concept_code,
    correct: it.answer === 'right',
    seconds: 60,
  }))
  try {
    const res = await api.diagnose({ student_id: store.studentId, answers })
    store.diagnoseResult = res
    message.success(res.mock ? '已用 mock 兜底返回' : '✓ LLM 诊断完成,即将查看结果')
    setTimeout(() => router.push('/path'), 700)
  } catch (e) {
    message.error('诊断失败: ' + e.message)
  } finally {
    diagnosing.value = false
  }
}
</script>
