<template>
  <div class="page-container">
    <h2 class="page-title">📋 学生画像录入</h2>

    <el-steps :active="currentStep" finish-status="success" align-center class="steps">
      <el-step title="基本信息" />
      <el-step title="学习偏好" />
      <el-step title="确认提交" />
    </el-steps>

    <div class="card" style="margin-top: 24px">
      <transition name="fade" mode="out-in">
        <div v-if="currentStep === 0" key="step1">
          <div class="card-title">基本信息</div>
          <el-form :model="form" label-width="100px" label-position="top">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="昵称" required>
                  <el-input v-model="form.nickname" placeholder="请输入昵称" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="学科">
                  <el-select v-model="form.subject" style="width: 100%">
                    <el-option label="管综数学" value="管综数学" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="学习目标">
                  <el-input v-model="form.learning_goal" placeholder="如：2027年管综数学过国家线" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="认知水平">
                  <el-radio-group v-model="form.cognitive_level">
                    <el-radio-button value="beginner">初级（离校多年）</el-radio-button>
                    <el-radio-button value="intermediate">中级（有基础）</el-radio-button>
                    <el-radio-button value="advanced">高级（系统学过）</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="每日可用学习时间">
              <el-slider v-model="form.available_minutes_per_day" :min="5" :max="180" :step="5" show-stops :format-tooltip="(v: number) => v + ' 分钟'" />
            </el-form-item>
          </el-form>
          <div class="step-actions">
            <el-button type="primary" @click="currentStep = 1" :disabled="!form.nickname">下一步 →</el-button>
          </div>
        </div>

        <div v-else-if="currentStep === 1" key="step2">
          <div class="card-title">学习偏好</div>
          <el-form :model="form" label-position="top">
            <el-form-item label="学习风格">
              <div class="style-cards">
                <div
                  v-for="s in styleOptions" :key="s.value"
                  class="style-card"
                  :class="{ active: form.learning_style === s.value }"
                  @click="form.learning_style = s.value"
                >
                  <div class="style-icon">{{ s.icon }}</div>
                  <div class="style-name">{{ s.label }}</div>
                </div>
              </div>
            </el-form-item>
          </el-form>
          <div class="step-actions">
            <el-button @click="currentStep = 0">← 上一步</el-button>
            <el-button type="primary" @click="currentStep = 2">下一步 →</el-button>
          </div>
        </div>

        <div v-else key="step3">
          <div class="card-title">确认画像</div>
          <div class="profile-summary">
            <div class="summary-avatar">👤</div>
            <div class="summary-info">
              <h3>{{ form.nickname }}</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="学科">{{ form.subject }}</el-descriptions-item>
                <el-descriptions-item label="目标">{{ form.learning_goal }}</el-descriptions-item>
                <el-descriptions-item label="认知水平">{{ levelMap[form.cognitive_level] }}</el-descriptions-item>
                <el-descriptions-item label="学习风格">{{ styleMap[form.learning_style] }}</el-descriptions-item>
                <el-descriptions-item label="日可用时间">{{ form.available_minutes_per_day }} 分钟</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <div class="step-actions">
            <el-button @click="currentStep = 1">← 上一步</el-button>
            <el-button type="primary" size="large" @click="submitProfile" :loading="submitting">✓ 提交画像</el-button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useStudentStore } from '@/stores'

const router = useRouter()
const studentStore = useStudentStore()
const currentStep = ref(0)
const submitting = ref(false)

const form = reactive({
  nickname: '',
  subject: '管综数学',
  cognitive_level: 'beginner' as 'beginner' | 'intermediate' | 'advanced',
  learning_goal: '',
  available_minutes_per_day: 60,
  learning_style: 'visual' as 'visual' | 'auditory' | 'kinesthetic' | 'reading',
})

const styleOptions = [
  { value: 'visual' as const, label: '视觉型', icon: '🎨' },
  { value: 'auditory' as const, label: '听觉型', icon: '🎧' },
  { value: 'reading' as const, label: '读写型', icon: '📝' },
  { value: 'kinesthetic' as const, label: '动觉型', icon: '🎮' }
]

const levelMap: Record<string, string> = { beginner: '初级', intermediate: '中级', advanced: '高级' }
const styleMap: Record<string, string> = { visual: '视觉型', auditory: '听觉型', reading: '读写型', kinesthetic: '动觉型' }

async function submitProfile() {
  submitting.value = true
  try {
    await studentStore.createProfile({
      nickname: form.nickname,
      subject: form.subject,
      cognitive_level: form.cognitive_level,
      learning_goal: form.learning_goal || '管综数学过国家线',
      available_minutes_per_day: form.available_minutes_per_day,
      learning_style: form.learning_style,
    })
    ElMessage.success(`画像提交成功！学生ID: ${studentStore.studentId}`)
    router.push('/diagnose')
  } catch {
    ElMessage.error('画像提交失败，请重试')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.steps {
  max-width: 600px;
  margin: 0 auto;
}
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}
.style-cards {
  display: flex;
  gap: 16px;
}
.style-card {
  width: 100px;
  height: 90px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}
.style-card:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
.style-card.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 0 0 3px rgba(64,158,255,0.2);
}
.style-icon {
  font-size: 28px;
  margin-bottom: 4px;
}
.style-name {
  font-size: 13px;
  color: #606266;
}
.profile-summary {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}
.summary-avatar {
  font-size: 48px;
  width: 80px;
  height: 80px;
  background: #f0f2f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.summary-info {
  flex: 1;
}
.summary-info h3 {
  font-size: 20px;
  margin-bottom: 12px;
}
</style>
