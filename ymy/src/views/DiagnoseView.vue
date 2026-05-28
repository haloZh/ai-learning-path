<template>
  <div class="page-container">
    <h2 class="page-title">🔍 诊断测验</h2>

    <template v-if="!diagnoseStore.isSubmitted">
      <template v-if="diagnoseStore.questions.length > 0">
        <div class="card">
          <div class="progress-row">
            <span>Q{{ currentIndex + 1 }} / {{ diagnoseStore.questions.length }}</span>
            <el-progress :percentage="progressPercent" :stroke-width="10" style="flex:1;margin:0 16px" />
          </div>
        </div>

        <div class="card question-card">
          <div class="question-meta">
            <el-tag size="small">{{ currentQuestion.concept_code }}</el-tag>
            <span class="difficulty">
              <span v-for="i in currentQuestion.difficulty" :key="i">⭐</span>
            </span>
            <el-tag v-if="currentQuestion.question_type === 'sufficient'" type="warning" size="small">条件充分判断</el-tag>
          </div>

          <div v-if="currentQuestion.question_type === 'sufficient'" class="sufficient-hint">
            <el-alert type="info" :closable="false" show-icon>
              <template #title>条件充分判断题</template>
              A: 条件(1)充分，(2)不充分 &nbsp; B: 条件(2)充分，(1)不充分 &nbsp; C: 联合充分 &nbsp; D: 各自都充分 &nbsp; E: 联合也不充分
            </el-alert>
          </div>

          <div class="question-stem">
            <KatexRender :content="currentQuestion.stem" />
          </div>

          <div class="question-options">
            <div
              v-for="(text, key) in currentQuestion.choices" :key="key"
              class="option-item"
              :class="{ selected: diagnoseStore.answers[currentQuestion.id] === key }"
              @click="selectAnswer(currentQuestion.id, key as string)"
            >
              <span class="option-key">{{ key }}.</span>
              <KatexRender :content="text" />
            </div>
          </div>

          <div class="question-nav">
            <el-button @click="prevQuestion" :disabled="currentIndex === 0">← 上一题</el-button>
            <el-button v-if="currentIndex < diagnoseStore.questions.length - 1" type="primary" @click="nextQuestion">下一题 →</el-button>
            <el-button v-else type="success" @click="submitDiagnose" :loading="diagnoseStore.isLoading">提交诊断</el-button>
          </div>
        </div>

        <div class="card answer-sheet">
          <div class="card-title">答题卡</div>
          <div class="sheet-grid">
            <div
              v-for="(q, i) in diagnoseStore.questions" :key="q.id"
              class="sheet-item"
              :class="{ answered: diagnoseStore.answers[q.id], current: i === currentIndex }"
              @click="currentIndex = i"
            >
              {{ i + 1 }}
            </div>
          </div>
        </div>
      </template>

      <div v-else class="card" style="text-align:center;padding:60px">
        <el-icon :size="40" color="#409eff"><Loading /></el-icon>
        <p style="margin-top:12px;color:#909399">正在加载诊断题目...</p>
      </div>
    </template>

    <template v-else>
      <div class="card">
        <div class="card-title">
          📊 诊断结果
          <el-tag v-if="diagnoseStore.isMock" type="warning" size="small" style="margin-left:8px">⚠️ Mock</el-tag>
          <el-tag v-else type="success" size="small" style="margin-left:8px">✓ LLM</el-tag>
        </div>
        <div class="result-grid">
          <div class="result-chart">
            <div ref="radarRef" style="width:100%;height:350px"></div>
          </div>
          <div class="result-detail">
            <div class="agent-analysis">
              <div class="agent-header">🤖 诊断 Agent 分析</div>
              <div class="agent-text" v-html="formattedReasoning"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">详细知识点掌握度</div>
        <div class="mastery-list">
          <div v-for="(val, key) in diagnoseStore.mastery" :key="key" class="mastery-item">
            <span class="mastery-name">{{ key }}</span>
            <el-progress
              :percentage="Math.round(val * 100)"
              :color="masteryColor(val)"
              :stroke-width="16"
              style="flex:1"
            />
            <el-tag :type="masteryTagType(val)" size="small">{{ masteryLabel(val) }}</el-tag>
          </div>
        </div>
      </div>

      <div class="card" style="text-align:center">
        <el-button type="primary" size="large" @click="goToPath">生成个性化路径 →</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useDiagnoseStore, usePathStore, useAssessStore, useStudentStore } from '@/stores'
import KatexRender from '@/components/KatexRender.vue'

const router = useRouter()
const diagnoseStore = useDiagnoseStore()
const pathStore = usePathStore()
const assessStore = useAssessStore()
const studentStore = useStudentStore()

const currentIndex = ref(0)
const radarRef = ref<HTMLElement>()

const currentQuestion = computed(() => diagnoseStore.questions[currentIndex.value] || diagnoseStore.questions[0])
const progressPercent = computed(() => {
  const total = diagnoseStore.questions.length
  if (!total) return 0
  return Math.round((Object.keys(diagnoseStore.answers).length / total) * 100)
})
const formattedReasoning = computed(() => diagnoseStore.reasoning.map(r => `• ${r}`).join('<br>'))

function selectAnswer(qid: number, answer: string) {
  diagnoseStore.setAnswer(qid, answer)
}

function prevQuestion() { if (currentIndex.value > 0) currentIndex.value-- }
function nextQuestion() { if (currentIndex.value < diagnoseStore.questions.length - 1) currentIndex.value++ }

async function submitDiagnose() {
  const unanswered = diagnoseStore.questions.length - Object.keys(diagnoseStore.answers).length
  if (unanswered > 0) {
    try {
      await ElMessageBox.confirm(`还有 ${unanswered} 题未作答，确定提交吗？`, '提示', { type: 'warning' })
    } catch { return }
  }

  const sid = studentStore.studentId
  if (!sid) {
    ElMessage.error('请先完成画像录入')
    router.push('/profile')
    return
  }

  try {
    const res = await diagnoseStore.submitDiagnose(sid)
    pathStore.setPath(res.path)
    assessStore.setFromDiagnose(res.mastery, res.path, res.reasoning, res.mock)
    ElMessage.success('诊断完成！')
    await nextTick()
    renderRadar()
  } catch {
    ElMessage.error('诊断提交失败，请重试')
  }
}

function masteryColor(v: number) {
  if (v >= 0.7) return '#67c23a'
  if (v >= 0.3) return '#e6a23c'
  return '#f56c6c'
}
function masteryTagType(v: number) {
  if (v >= 0.7) return 'success'
  if (v >= 0.3) return 'warning'
  return 'danger'
}
function masteryLabel(v: number) {
  if (v >= 0.7) return '已掌握'
  if (v >= 0.3) return '薄弱'
  if (v > 0) return '极弱'
  return '未学'
}

function renderRadar() {
  if (!radarRef.value) return
  const chart = echarts.init(radarRef.value)
  const mastery = diagnoseStore.mastery
  const categories: Record<string, number[]> = { '算术': [], '代数': [], '几何': [], '数据分析': [] }
  for (const [k, v] of Object.entries(mastery)) {
    if (k.startsWith('算术')) categories['算术'].push(v)
    else if (k.startsWith('代数')) categories['代数'].push(v)
    else if (k.startsWith('几何')) categories['几何'].push(v)
    else categories['数据分析'].push(v)
  }
  const modules = Object.keys(categories)
  const avgValues = modules.map(m => {
    const arr = categories[m]
    return arr.length ? Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 100) : 0
  })
  chart.setOption({
    tooltip: {},
    radar: { indicator: modules.map(m => ({ name: m, max: 100 })), shape: 'polygon', splitNumber: 5 },
    series: [{
      type: 'radar',
      data: [{
        value: avgValues, name: '掌握度',
        areaStyle: { color: 'rgba(64,158,255,0.2)' },
        lineStyle: { color: '#409eff', width: 2 },
        itemStyle: { color: '#409eff' }
      }]
    }]
  })
}

function goToPath() {
  router.push('/path')
}

onMounted(async () => {
  if (diagnoseStore.questions.length === 0) {
    try {
      await diagnoseStore.fetchQuestions(5)
    } catch {
      ElMessage.error('加载题目失败，请检查后端服务')
    }
  }
  if (diagnoseStore.isSubmitted) {
    nextTick(() => renderRadar())
  }
})

watch(() => diagnoseStore.isSubmitted, (val) => {
  if (val) nextTick(() => renderRadar())
})
</script>

<style scoped>
.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #606266;
}
.question-card {
  min-height: 400px;
}
.question-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.difficulty {
  font-size: 12px;
}
.sufficient-hint {
  margin-bottom: 16px;
}
.question-stem {
  font-size: 16px;
  line-height: 1.8;
  margin-bottom: 20px;
}
.question-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}
.option-item {
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.option-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
.option-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
  color: #409eff;
  font-weight: 500;
}
.option-key {
  font-weight: 600;
  flex-shrink: 0;
}
.question-nav {
  display: flex;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}
.answer-sheet .sheet-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.sheet-item {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.sheet-item.answered {
  background: #67c23a;
  color: #fff;
  border-color: #67c23a;
}
.sheet-item.current {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64,158,255,0.2);
}
.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.agent-analysis {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}
.agent-header {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}
.agent-text {
  font-size: 14px;
  line-height: 2;
  color: #606266;
}
.mastery-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.mastery-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.mastery-name {
  width: 120px;
  font-size: 13px;
  text-align: right;
  flex-shrink: 0;
}
</style>
