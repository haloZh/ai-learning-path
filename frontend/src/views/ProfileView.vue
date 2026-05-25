<template>
  <div class="card">
    <h2>① 学生画像</h2>
    <p class="hint">填写学生的基本信息和学习偏好,作为后续诊断和路径规划的输入。</p>

    <div class="row">
      <span><label>昵称</label><input type="text" v-model="form.nickname" /></span>
      <span><label>学科</label><input type="text" v-model="form.subject" /></span>
    </div>
    <div class="row">
      <span>
        <label>认知层</label>
        <select v-model="form.cognitive_level">
          <option value="beginner">初学(beginner)</option>
          <option value="intermediate">进阶(intermediate)</option>
          <option value="advanced">熟练(advanced)</option>
        </select>
      </span>
      <span>
        <label>学习风格</label>
        <select v-model="form.learning_style">
          <option value="reading">阅读(reading)</option>
          <option value="visual">视觉(visual)</option>
          <option value="auditory">听觉(auditory)</option>
          <option value="kinesthetic">动手(kinesthetic)</option>
        </select>
      </span>
      <span>
        <label>每日时间</label>
        <input type="number" v-model.number="form.available_minutes_per_day" min="5" max="600" style="width: 80px" /> 分钟
      </span>
    </div>
    <div class="row">
      <span style="flex: 1; min-width: 100%">
        <label>学习目标</label>
        <input type="text" v-model="form.learning_goal" style="width: 70%" />
      </span>
    </div>

    <button :disabled="creating" @click="onCreate">
      {{ creating ? '创建中...' : '创建学生画像' }}
    </button>
    <span v-if="status.text" :class="['status', status.kind]">{{ status.text }}</span>
  </div>

  <div v-if="store.studentId" class="nav-foot">
    <span class="hint">已创建,准备进入下一步</span>
    <button @click="$router.push('/diagnose')">进入答题 →</button>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { store } from '../store'

const router = useRouter()
const creating = ref(false)
const status = reactive({ text: '', kind: 'ok' })

const form = reactive({
  nickname: '演示同学',
  subject: '管综数学',
  cognitive_level: 'intermediate',
  learning_style: 'reading',
  available_minutes_per_day: 60,
  learning_goal: '2027 年管综数学过国家线',
})

async function onCreate() {
  creating.value = true
  status.text = '创建中...'
  status.kind = 'warn'
  try {
    const stu = await api.createProfile({ ...form })
    store.studentId = stu.id
    store.studentNickname = stu.nickname
    status.text = `✓ 创建成功 student_id=${stu.id}`
    status.kind = 'ok'
    // 自动跳转下一步(给老师演示节奏)
    setTimeout(() => router.push('/diagnose'), 600)
  } catch (e) {
    status.text = '✗ ' + e.message
    status.kind = 'bad'
  } finally {
    creating.value = false
  }
}
</script>
