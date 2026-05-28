<template>
  <template v-if="!store.diagnoseResult">
    <n-card>
      <n-empty description="请先完成第 2 步答题并提交诊断">
        <template #extra>
          <n-button type="primary" @click="$router.push('/diagnose')">返回答题</n-button>
        </template>
      </n-empty>
    </n-card>
  </template>

  <template v-else>
    <n-card title="🎯 诊断结果">
      <template #header-extra>
        <n-tag round :bordered="false" type="warning">第 3 步</n-tag>
      </template>

      <n-alert
        :type="store.diagnoseResult.mock ? 'warning' : 'success'"
        :show-icon="true"
        style="margin-bottom: 18px"
      >
        {{ store.diagnoseResult.mock
          ? '本次链路走了 mock 兜底(可能是 LLM 不可用)'
          : '由真实 LLM(火山方舟 Doubao) + RAG(bge-m3 / Chroma) 生成'
        }}
      </n-alert>

      <div v-if="evaluation" class="evaluation-card">
        <div class="eval-head">
          <span class="eval-title">📊 路径质量评分</span>
          <span class="eval-score" :class="scoreClass(evaluation.score)">
            {{ evaluation.score }}<small>/100</small>
          </span>
        </div>
        <div class="eval-grid">
          <div v-for="(label, key) in EVAL_KEYS" :key="key" class="eval-item">
            <span class="eval-label">{{ label }}</span>
            <span class="eval-bar">
              <span
                :style="{ width: ((evaluation.scores?.[key] ?? 0) * 10) + '%' }"
                :class="scoreSubClass(evaluation.scores?.[key])"
              ></span>
            </span>
            <span class="eval-num">{{ evaluation.scores?.[key] ?? '-' }}</span>
          </div>
        </div>
        <div v-if="evaluation.summary" class="eval-summary">📝 {{ evaluation.summary }}</div>
        <div v-if="evaluation.strengths" class="eval-line eval-strength">
          <b>亮点:</b> {{ evaluation.strengths }}
        </div>
        <div v-if="evaluation.improvements" class="eval-line eval-improve">
          <b>待改进:</b> {{ evaluation.improvements }}
        </div>
      </div>

      <div class="section-title">🩺 知识点掌握度</div>
      <div>
        <div v-for="[code, val] in masteryEntries" :key="code" class="mastery-row">
          <span class="code">{{ code }}</span>
          <span class="val">{{ Number(val ?? 0).toFixed(2) }}</span>
          <span class="bar">
            <span
              :class="masteryClass(val ?? 0)"
              :style="{ width: (Math.max(0, Math.min(1, Number(val ?? 0))) * 100).toFixed(0) + '%' }"
            ></span>
          </span>
        </div>
      </div>

      <div class="section-title">🗺️ 推荐学习路径</div>
      <div ref="pathEl" class="path-list">
        <div v-for="(p, i) in store.diagnoseResult.path" :key="i" class="path-item">
          <span class="seq">{{ i + 1 }}</span>
          <div class="body">
            <div class="title">{{ p.title }}</div>
            <div class="meta">
              <span>⏱ {{ p.estimated_minutes }} 分钟</span>
              <span>🏷 {{ p.concept_id }}</span>
            </div>
            <div class="reason">💡 {{ p.reason }}</div>
          </div>
        </div>
      </div>

      <div class="section-title">🧠 推理日志</div>
      <div class="reasoning-log">
        <div v-for="(line, i) in store.diagnoseResult.reasoning" :key="i" class="line">{{ line }}</div>
      </div>
    </n-card>

    <n-space justify="space-between" style="margin-top: 18px">
      <n-button @click="$router.push('/diagnose')">← 返回答题</n-button>
      <n-button type="primary" size="large" @click="$router.push('/study')">
        进入学习交互 →
      </n-button>
    </n-space>
  </template>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { store } from '../store'
import { renderKatex } from '../utils/katex'

const pathEl = ref(null)

const EVAL_KEYS = {
  targeting: '针对性',
  ordering: '顺序合理性',
  feasibility: '可行性',
  personalization: '个性化',
  resource_match: '资源匹配',
}

const masteryEntries = computed(() => {
  const m = store.diagnoseResult?.mastery || {}
  return Object.entries(m).sort((a, b) => (a[1] ?? 0) - (b[1] ?? 0))
})

const evaluation = computed(() => store.diagnoseResult?.evaluation || null)

function masteryClass(v) {
  const x = Number(v ?? 0)
  if (x < 0.4) return 'low'
  if (x < 0.7) return 'mid'
  return 'high'
}

function scoreClass(score) {
  if (score == null) return ''
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-mid'
  return 'score-low'
}

function scoreSubClass(v) {
  if (v == null) return ''
  if (v >= 8) return 'high'
  if (v >= 5) return 'mid'
  return 'low'
}

async function rerender() {
  await nextTick()
  renderKatex(pathEl.value)
}

onMounted(rerender)

watch(
  () => store.diagnoseResult?.path,
  () => { rerender() },
  { deep: false },
)
</script>
