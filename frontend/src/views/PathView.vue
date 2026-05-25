<template>
  <div v-if="!store.diagnoseResult" class="card">
    <p class="hint">请先完成 ② 模拟答卷并提交诊断。</p>
    <button @click="$router.push('/diagnose')">返回答题</button>
  </div>

  <template v-else>
    <div class="card">
      <h2>③ 诊断结果</h2>
      <div :class="['status', store.diagnoseResult.mock ? 'warn' : 'ok']" style="margin-left: 0">
        {{ store.diagnoseResult.mock ? '⚠️ 本次链路走了 mock 兜底' : '✓ 由真实 LLM (Doubao) 生成' }}
      </div>

      <h3>知识点掌握度</h3>
      <div>
        <div
          v-for="[code, val] in masteryEntries"
          :key="code"
          class="mastery-row"
        >
          <span class="code">{{ code }}</span>
          <span class="val">{{ val.toFixed(2) }}</span>
          <span class="bar"><span :style="{ width: (val * 100).toFixed(0) + '%' }"></span></span>
        </div>
      </div>

      <h3>推荐学习路径</h3>
      <div ref="pathEl">
        <div
          v-for="(p, i) in store.diagnoseResult.path"
          :key="i"
          class="path-item"
        >
          <div class="title">{{ i + 1 }}. {{ p.title }}</div>
          <div class="meta">{{ p.estimated_minutes }} 分钟 · {{ p.concept_id }}</div>
          <div class="reason">{{ p.reason }}</div>
        </div>
      </div>

      <h3>推理日志</h3>
      <div class="reasoning">
        <div v-for="(line, i) in store.diagnoseResult.reasoning" :key="i">{{ line }}</div>
      </div>
    </div>

    <div class="nav-foot">
      <button class="secondary" @click="$router.push('/diagnose')">← 返回答题</button>
      <button @click="$router.push('/study')">进入学习交互 →</button>
    </div>
  </template>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { store } from '../store'
import { renderKatex } from '../utils/katex'

const pathEl = ref(null)

const masteryEntries = computed(() => {
  const m = store.diagnoseResult?.mastery || {}
  return Object.entries(m).sort((a, b) => a[1] - b[1])
})

onMounted(async () => {
  await nextTick()
  renderKatex(pathEl.value)
})
</script>
