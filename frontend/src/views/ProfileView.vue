<template>
  <n-card title="📋 学生画像">
    <template #header-extra>
      <n-tag round :bordered="false" type="warning">第 1 步</n-tag>
    </template>

    <n-text depth="3" style="font-size: 13px">
      填写学生的基本信息和学习偏好,作为后续诊断和路径规划的输入。
    </n-text>

    <n-grid :cols="2" :x-gap="20" :y-gap="14" style="margin-top: 16px">
      <n-gi>
        <n-form-item label="昵称">
          <n-input v-model:value="form.nickname" placeholder="例如: 张三" />
        </n-form-item>
      </n-gi>
      <n-gi>
        <n-form-item label="学科">
          <n-input v-model:value="form.subject" />
        </n-form-item>
      </n-gi>
      <n-gi>
        <n-form-item label="认知层">
          <n-select v-model:value="form.cognitive_level" :options="cognitiveOptions" />
        </n-form-item>
      </n-gi>
      <n-gi>
        <n-form-item label="学习风格">
          <n-select v-model:value="form.learning_style" :options="styleOptions" />
        </n-form-item>
      </n-gi>
      <n-gi>
        <n-form-item label="每日学习时间">
          <n-input-number
            v-model:value="form.available_minutes_per_day"
            :min="5"
            :max="600"
            style="width: 100%"
          >
            <template #suffix>分钟</template>
          </n-input-number>
        </n-form-item>
      </n-gi>
      <n-gi :span="2">
        <n-form-item label="学习目标">
          <n-input v-model:value="form.learning_goal" type="text" />
        </n-form-item>
      </n-gi>
    </n-grid>

    <n-space>
      <n-button type="primary" :loading="creating" size="large" @click="onCreate">
        🚀 创建学生画像
      </n-button>
      <n-tag v-if="store.studentId" :bordered="false" type="success" round>
        ✓ 已创建 student_id = {{ store.studentId }}
      </n-tag>
    </n-space>
  </n-card>

  <n-space justify="end" style="margin-top: 18px" v-if="store.studentId">
    <n-button type="primary" size="large" @click="$router.push('/diagnose')">
      进入答题 →
    </n-button>
  </n-space>
</template>

<script setup>
import { reactive, ref, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { api } from '../api'
import { store } from '../store'

const router = useRouter()
const message = useMessage()
const creating = ref(false)

const form = reactive({
  nickname: '演示同学',
  subject: '管综数学',
  cognitive_level: 'intermediate',
  learning_style: 'reading',
  available_minutes_per_day: 60,
  learning_goal: '2027 年管综数学过国家线',
})

const cognitiveOptions = [
  { label: '初学(beginner)', value: 'beginner' },
  { label: '进阶(intermediate)', value: 'intermediate' },
  { label: '熟练(advanced)', value: 'advanced' },
]
const styleOptions = [
  { label: '阅读(reading)', value: 'reading' },
  { label: '视觉(visual)', value: 'visual' },
  { label: '听觉(auditory)', value: 'auditory' },
  { label: '动手(kinesthetic)', value: 'kinesthetic' },
]

async function onCreate() {
  creating.value = true
  try {
    const stu = await api.createProfile({ ...form })
    store.studentId = stu.id
    store.studentNickname = stu.nickname
    message.success(`画像创建成功 (id=${stu.id}),即将进入答题`)
    setTimeout(() => router.push('/diagnose'), 700)
  } catch (e) {
    message.error('创建失败: ' + e.message)
  } finally {
    creating.value = false
  }
}
</script>
