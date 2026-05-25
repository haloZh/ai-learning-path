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
    <n-card title="🔄 学习交互(动态调整)">
      <template #header-extra>
        <n-tag round :bordered="false" type="warning">第 4 步</n-tag>
      </template>

      <n-text depth="3" style="font-size: 13px">
        学生在学习中遇到问题、或已掌握某节点时,反馈给系统,
        优化 Agent 会调用 LLM 重新规划路径。
      </n-text>

      <n-grid :cols="2" :x-gap="20" :y-gap="14" style="margin-top: 16px">
        <n-gi>
          <n-form-item label="知识点">
            <n-select
              v-model:value="form.concept_id"
              :options="conceptOptions"
              filterable
              placeholder="选择一个知识点"
            />
          </n-form-item>
        </n-gi>
        <n-gi>
          <n-form-item label="事件类型">
            <n-radio-group v-model:value="form.event">
              <n-radio-button value="struggle">😖 卡住</n-radio-button>
              <n-radio-button value="mastered">😎 已掌握</n-radio-button>
              <n-radio-button value="skip">⏭ 跳过</n-radio-button>
            </n-radio-group>
          </n-form-item>
        </n-gi>
        <n-gi :span="2">
          <n-form-item label="具体反馈">
            <n-input v-model:value="form.detail" placeholder="例如:判别式总是算错" />
          </n-form-item>
        </n-gi>
      </n-grid>

      <n-button type="primary" size="large" :loading="submitting" @click="onSubmit">
        💬 提交反馈,让 AI 调整路径
      </n-button>
    </n-card>

    <n-card title="🗺️ 当前学习路径" style="margin-top: 14px">
      <template #header-extra>
        <n-tag v-if="lastUpdate" :bordered="false" type="success" round>
          路径已更新 · {{ lastUpdate }}
        </n-tag>
      </template>

      <div ref="pathEl" class="path-list">
        <div
          v-for="(p, i) in store.diagnoseResult.path"
          :key="i + '-' + p.title"
          :class="['path-item', { 'is-new': newIndices.has(i) }]"
        >
          <span class="seq">{{ i + 1 }}</span>
          <div class="body">
            <div class="title">
              {{ p.title }}
              <n-tag
                v-if="newIndices.has(i)"
                size="small"
                type="success"
                :bordered="false"
                style="margin-left: 8px"
              >🆕 新增</n-tag>
            </div>
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
        <div
          v-for="(line, i) in store.diagnoseResult.reasoning"
          :key="i"
          :class="['line', line.startsWith('[interaction]') && 'optimize']"
        >{{ line }}</div>
      </div>
    </n-card>

    <n-space justify="start" style="margin-top: 18px">
      <n-button @click="$router.push('/path')">← 看诊断结果</n-button>
    </n-space>
  </template>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { api } from '../api'
import { store } from '../store'
import { renderKatex } from '../utils/katex'

const message = useMessage()
const pathEl = ref(null)
const submitting = ref(false)
const lastUpdate = ref('')
const newIndices = ref(new Set())

const form = reactive({
  concept_id: '',
  event: 'struggle',
  detail: '判别式总是算错',
})

const conceptOptions = computed(() =>
  store.conceptOptions.map((c) => ({ label: c.code, value: c.code })),
)

onMounted(async () => {
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
  try {
    const oldTitles = new Set(store.diagnoseResult.path.map((p) => p.title))
    const res = await api.postInteraction({
      student_id: store.studentId,
      event: form.event,
      concept_id: form.concept_id,
      detail: form.detail || null,
    })
    const newSet = new Set()
    res.path.forEach((p, i) => {
      if (!oldTitles.has(p.title)) newSet.add(i)
    })
    newIndices.value = newSet
    store.diagnoseResult.path = res.path
    if (res.reasoning) {
      res.reasoning.forEach((line) => {
        store.diagnoseResult.reasoning.push('[interaction] ' + line)
      })
    }
    lastUpdate.value = new Date().toLocaleTimeString('zh-CN', { hour12: false })
    message.success(res.mock ? '已用 mock 兜底' : `路径已更新 (新增 ${newSet.size} 项)`)
    await nextTick()
    renderKatex(pathEl.value)
  } catch (e) {
    message.error('提交失败: ' + e.message)
  } finally {
    submitting.value = false
  }
}
</script>
