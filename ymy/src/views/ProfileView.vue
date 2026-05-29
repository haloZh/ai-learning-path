<template>
  <div class="page-container">
    <h2 class="page-title">📋 学生画像录入</h2>

    <el-steps :active="currentStep" finish-status="success" align-center class="steps">
      <el-step title="基本信息与偏好" />
      <el-step title="确认提交" />
    </el-steps>

    <div class="card" style="margin-top: 24px">
      <transition name="fade" mode="out-in">
        <div v-if="currentStep === 0" key="step1">
          <div class="card-title">基本信息与学习偏好</div>
          <el-form :model="form" label-position="top">
            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="昵称" required>
                  <el-input v-model="form.nickname" placeholder="请输入昵称" maxlength="20" show-word-limit />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="学科">
                  <el-input :value="form.subject" readonly>
                    <template #append>已锁定</template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="24">
              <el-col :span="12">
                <el-form-item label="学习目标" required>
                  <el-select
                    v-model="form.learning_goal"
                    placeholder="请选择或输入学习目标"
                    filterable
                    allow-create
                    default-first-option
                    style="width: 100%"
                  >
                    <el-option v-for="opt in goalOptions" :key="opt" :label="opt" :value="opt" />
                  </el-select>
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
              <div class="time-row">
                <el-slider
                  v-model="form.available_minutes_per_day"
                  :min="15"
                  :max="180"
                  :step="5"
                  style="flex: 1"
                />
                <span class="time-value">{{ form.available_minutes_per_day }} 分钟</span>
              </div>
              <div class="time-presets">
                <el-button
                  v-for="m in [30, 60, 90, 120]"
                  :key="m"
                  size="small"
                  :type="form.available_minutes_per_day === m ? 'primary' : 'default'"
                  @click="form.available_minutes_per_day = m"
                >{{ m }} 分钟</el-button>
              </div>
            </el-form-item>

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
                  <div class="style-desc">{{ s.desc }}</div>
                </div>
              </div>
            </el-form-item>
          </el-form>

          <div class="step-actions">
            <el-button
              type="primary"
              size="large"
              :disabled="!canNext"
              @click="currentStep = 1"
            >下一步 →</el-button>
          </div>
        </div>

        <div v-else key="step2">
          <div class="card-title">确认画像</div>
          <div class="profile-summary">
            <div class="summary-avatar">{{ styleOptions.find(s=>s.value===form.learning_style)?.icon || '👤' }}</div>
            <div class="summary-info">
              <h3>{{ form.nickname }}</h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="学科">{{ form.subject }}</el-descriptions-item>
                <el-descriptions-item label="学习目标">{{ form.learning_goal }}</el-descriptions-item>
                <el-descriptions-item label="认知水平">{{ levelMap[form.cognitive_level] }}</el-descriptions-item>
                <el-descriptions-item label="学习风格">{{ styleMap[form.learning_style] }}</el-descriptions-item>
                <el-descriptions-item label="日可用时间" :span="2">{{ form.available_minutes_per_day }} 分钟</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <div class="step-actions">
            <el-button @click="currentStep = 0">← 上一步</el-button>
            <el-button type="primary" size="large" @click="submitProfile" :loading="submitting">✓ 创建画像并开始诊断</el-button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
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
  // 默认初级:大多数管综考生离校多年,默认贴近真实场景
  cognitive_level: 'beginner' as 'beginner' | 'intermediate' | 'advanced',
  learning_goal: '',
  available_minutes_per_day: 60,
  learning_style: 'visual' as 'visual' | 'auditory' | 'kinesthetic' | 'reading',
})

const canNext = computed(() => !!form.nickname.trim() && !!form.learning_goal.trim())

const styleOptions = [
  { value: 'visual' as const, label: '视觉型', icon: '🎨', desc: '偏好图表/视频' },
  { value: 'auditory' as const, label: '听觉型', icon: '🎧', desc: '偏好音频/讲解' },
  { value: 'reading' as const, label: '读写型', icon: '📝', desc: '偏好教材/笔记' },
  { value: 'kinesthetic' as const, label: '动觉型', icon: '🎮', desc: '偏好做题/实操' },
]

const goalOptions = [
  '2027 年管综数学过国家线',
  '2027 年管综数学冲 60+',
  '2026 年管综数学过国家线',
  '半年内系统补强管综数学',
  '冲刺阶段精准补强薄弱点',
  '突破管综数学及格线',
]

const levelMap: Record<string, string> = { beginner: '初级（离校多年）', intermediate: '中级（有基础）', advanced: '高级（系统学过）' }
const styleMap: Record<string, string> = { visual: '视觉型', auditory: '听觉型', reading: '读写型', kinesthetic: '动觉型' }

async function submitProfile() {
  submitting.value = true
  try {
    await studentStore.createProfile({
      nickname: form.nickname.trim(),
      subject: form.subject,
      cognitive_level: form.cognitive_level,
      learning_goal: form.learning_goal.trim(),
      available_minutes_per_day: form.available_minutes_per_day,
      learning_style: form.learning_style,
    })
    ElMessage.success('画像创建成功，进入诊断测验')
    router.push('/diagnose')
  } catch {
    ElMessage.error('画像提交失败，请检查后端服务后重试')
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
.time-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.time-value {
  min-width: 90px;
  text-align: right;
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}
.time-presets {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.style-cards {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.style-card {
  flex: 1;
  min-width: 130px;
  padding: 14px 12px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.25s;
  background: #fff;
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
  font-size: 32px;
  margin-bottom: 6px;
}
.style-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}
.style-desc {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
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
