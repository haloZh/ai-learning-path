<template>
  <div v-if="!store.diagnoseResult" class="card">
    <p class="hint">请先完成 ② 模拟答卷并提交诊断。</p>
    <button @click="$router.push('/diagnose')">返回答题</button>
  </div>

  <template v-else>
    <div class="card">
      <h2>④ 学习交互(动态调整)</h2>
      <p class="hint">学生在学习中遇到问题、或已掌握某节点时,反馈给系统,优化 Agent 重新规划路径。</p>

      <div class="row">
        <span>
          <label>知识点</label>
          <select v-model="form.concept_id" style="min-width: 240px">
            <option v-for="c in store.conceptOptions" :key="c.code" :value="c.code">
              {{ c.code }}
            </option>
          </select>
        </span>
        <span>
          <label>事件</label>
          <select v-model="form.event">
            <option value="struggle">struggle - 卡住,讲解不清</option>
            <option value="mastered">mastered - 已掌握</option>
            <option value="skip">skip - 暂时跳过</option>
          </select>
        </span>
      </div>
      <div class="row">
        <span style="flex: 1; min-width: 100%">
          <label>具体反馈</label>
          <input type="text" v-model="form.detail" style="width: 70%" />
        </span>
      </div>

      <button :disabled="submitting" @click="onSubmit">
        {{ submitting ? '调用优化 Agent...' : '提交反馈' }}
      </button>
      <span v-if="status.text" :class="['status', status.kind]">{{ status.text }}</span>
    </div>

    <div class="card">
      <h3>当前学习路径</h3>
      <div ref="pathEl">
        <div
          v-for="(p, i) in store.diagnoseResult.path"
          :key="i + '-' + p.title"
          :class="['path-item', { 'is-new': newIndices.has(i) }]"
        >
          <div class="title">{{ i + 1 }}. {{ p.title }}</div>
          <div class="meta">{{ p.estimated_minutes }} 分钟 · {{ p.concept_id }}</div>
          <div class="reason">{{ p.reason }}</div>
        </div>
      </div>

      <h3>推理日志</h3>
      <div class="reasoning">
        <div
          v-for="(line, i) in store.diagnoseResult.reasoning"
          :key="i"
          :class="{ highlight: line.startsWith('[interaction]') }"
        >{{ line }}</div>
      </div>
    </div>

    <div class="nav-foot">
      <button class="secondary" @click="$router.push('/path')">← 看诊断结果</button>
    </div>
  </template>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { store } from '../store'
import { renderKatex } from '../utils/katex'

const pathEl = ref(null)
const submitting = ref(false)
const status = reactive({ text: '', kind: 'ok' })
const newIndices = ref(new Set())

const form = reactive({
  concept_id: '',
  event: 'struggle',
  detail: '判别式总是算错',
})

onMounted(async () => {
  // 加载 concept 列表 + 默认选最低 mastery 那个
  if (store.conceptOptions.length === 0) {
    try {
      store.conceptOptions = await api.listConcepts('管综数学')
    } catch (e) {
      console.error(e)
    }
  }
  const m = store.diagnoseResult?.mastery || {}
  const lowest = Object.entries(m).sort((a, b) => a[1] - b[1])[0]
  if (lowest) form.concept_id = lowest[0]
  await nextTick()
  renderKatex(pathEl.value)
})

async function onSubmit() {
  submitting.value = true
  status.text = '调用 optimize Agent (LLM)...'
  status.kind = 'warn'
  try {
    const oldTitles = new Set(store.diagnoseResult.path.map((p) => p.title))
    const res = await api.postInteraction({
      student_id: store.studentId,
      event: form.event,
      concept_id: form.concept_id,
      detail: form.detail || null,
    })
    // 找出 res.path 中相对老路径"新增"的项
    const newSet = new Set()
    res.path.forEach((p, i) => {
      if (!oldTitles.has(p.title)) newSet.add(i)
    })
    newIndices.value = newSet

    store.diagnoseResult.path = res.path
    if (res.reasoning) {
      // 把 optimize 这一轮的 reasoning 末尾附加到现有的(打 [interaction] 前缀方便高亮)
      res.reasoning.forEach((line) => {
        store.diagnoseResult.reasoning.push('[interaction] ' + line)
      })
    }
    status.text = res.mock ? '⚠️ mock 兜底' : '✓ 路径已更新(新增项黄色高亮)'
    status.kind = res.mock ? 'warn' : 'ok'

    await nextTick()
    renderKatex(pathEl.value)
  } catch (e) {
    status.text = '✗ ' + e.message
    status.kind = 'bad'
  } finally {
    submitting.value = false
  }
}
</script>
