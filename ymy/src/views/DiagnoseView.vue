<template>
  <div class="page-container">
    <h2 class="page-title">🔍 诊断测验</h2>

    <!-- 全屏 loading 蒙版:多 Agent 协作总耗时 ~30-60s,分阶段显示进度 -->
    <div v-if="diagnoseStore.isLoading" class="diagnose-loading-mask">
      <div class="loading-card">
        <el-icon :size="40" class="rotate" color="#409eff"><Loading /></el-icon>
        <div class="loading-title">{{ loadingStages[loadingStage].title }}</div>
        <div class="loading-desc">{{ loadingStages[loadingStage].desc }}</div>
        <div class="loading-progress">
          <div
            v-for="(s, i) in loadingStages"
            :key="i"
            class="stage-dot"
            :class="{ done: i < loadingStage, active: i === loadingStage }"
          >
            <span class="dot-num">{{ i + 1 }}</span>
            <span class="dot-label">{{ s.short }}</span>
          </div>
        </div>
        <div class="loading-elapsed">已耗时 {{ elapsed }}s</div>
      </div>
    </div>

    <template v-if="!diagnoseStore.isSubmitted">
      <div class="card config-bar">
        <div class="config-left">
          <span class="config-label">抽题数量</span>
          <el-radio-group :model-value="qCount" size="small" @change="onQCountChange">
            <el-radio-button :value="5">5 题</el-radio-button>
            <el-radio-button :value="10">10 题</el-radio-button>
            <el-radio-button :value="15">15 题</el-radio-button>
          </el-radio-group>
          <el-button size="small" :loading="loading" @click="onReloadClick">🎲 重新抽题</el-button>
        </div>
        <div class="config-right" v-if="diagnoseStore.questions.length > 0">
          <el-tag v-if="unansweredCount > 0" type="warning" size="small">
            未答 {{ unansweredCount }} 题
          </el-tag>
          <el-tag v-else type="success" size="small">
            ✓ 全部已答
          </el-tag>
        </div>
      </div>

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
              <span v-for="i in currentQuestion.difficulty || 1" :key="i">⭐</span>
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
              v-for="c in normalizeChoices(currentQuestion.choices)" :key="c.key"
              class="option-item"
              :class="{ selected: diagnoseStore.answers[currentQuestion.id] === c.key }"
              @click="selectAnswer(currentQuestion.id, c.key)"
            >
              <span class="option-key">{{ c.key }}.</span>
              <KatexRender :content="c.text" />
            </div>
          </div>

          <div class="question-nav">
            <el-button @click="prevQuestion" :disabled="currentIndex === 0">← 上一题</el-button>
            <el-button v-if="currentIndex < diagnoseStore.questions.length - 1" type="primary" @click="nextQuestion">下一题 →</el-button>
            <el-button v-else type="success" size="large" @click="submitDiagnose" :loading="diagnoseStore.isLoading">🩺 提交诊断</el-button>
          </div>
        </div>

        <div class="card answer-sheet">
          <div class="card-title">
            答题卡
            <span class="sheet-legend">
              <span class="legend"><span class="ld ld-done"></span> 已答</span>
              <span class="legend"><span class="ld ld-todo"></span> 未答</span>
              <span class="legend"><span class="ld ld-cur"></span> 当前</span>
            </span>
          </div>
          <div class="sheet-grid">
            <div
              v-for="(q, i) in diagnoseStore.questions" :key="q.id"
              class="sheet-item"
              :class="{
                answered: diagnoseStore.answers[q.id],
                unanswered: !diagnoseStore.answers[q.id],
                current: i === currentIndex,
              }"
              @click="goTo(i)"
            >
              {{ i + 1 }}
            </div>
          </div>
        </div>
      </template>

      <div v-else class="card" style="text-align:center;padding:60px">
        <el-icon :size="40" color="#409eff" :class="{ rotate: loading }"><Loading /></el-icon>
        <p style="margin-top:12px;color:#909399">{{ loading ? '正在抽题...' : '点击"重新抽题"开始' }}</p>
      </div>
    </template>

    <template v-else>
      <div class="card">
        <div class="card-title">
          📊 诊断结果
          <el-tag v-if="diagnoseStore.isMock" type="warning" size="small" style="margin-left:8px">⚠️ Mock 兜底</el-tag>
          <el-tag v-else type="success" size="small" style="margin-left:8px">✓ LLM 真实输出</el-tag>
        </div>

        <div class="result-grid">
          <div class="result-chart">
            <div class="sub-title">📡 四大模块掌握度雷达</div>
            <div ref="radarRef" style="width:100%;height:320px"></div>
          </div>
          <div class="result-detail">
            <div class="sub-title">🤖 诊断 Agent 推理</div>
            <div class="agent-text">
              <div v-for="(line, i) in diagnoseStore.reasoning" :key="i" class="reason-line">• {{ line }}</div>
            </div>
          </div>
        </div>
      </div>

      <EvaluationCard v-if="diagnoseStore.evaluation" :evaluation="diagnoseStore.evaluation" />

      <div class="card">
        <div class="card-title">详细知识点掌握度</div>
        <div class="mastery-list">
          <div v-for="(val, key) in sortedMastery" :key="key" class="mastery-item">
            <span class="mastery-name">{{ key }}</span>
            <el-progress
              :percentage="Math.round((val ?? 0) * 100)"
              :color="masteryColor(val ?? 0)"
              :stroke-width="16"
              style="flex:1"
            />
            <el-tag :type="masteryTagType(val ?? 0)" size="small">{{ masteryLabel(val ?? 0) }}</el-tag>
          </div>
        </div>
      </div>

      <div class="card" style="text-align:center">
        <el-button @click="restartDiagnose" style="margin-right:12px">↻ 重新诊断</el-button>
        <el-button type="primary" size="large" @click="goToPath">查看个性化路径 →</el-button>
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
import EvaluationCard from '@/components/EvaluationCard.vue'

const router = useRouter()
const diagnoseStore = useDiagnoseStore()
const pathStore = usePathStore()
const assessStore = useAssessStore()
const studentStore = useStudentStore()

const currentIndex = ref(0)
const radarRef = ref<HTMLElement>()
const qCount = ref(5)
const loading = ref(false)

// 诊断进度感(伪进度,仅 UX,不真实接 SSE)
const loadingStage = ref(0)
const elapsed = ref(0)
let stageTimer: ReturnType<typeof setInterval> | null = null
let elapsedTimer: ReturnType<typeof setInterval> | null = null

const loadingStages = [
  { short: '诊断', title: '🤖 诊断 Agent 分析中…', desc: '基于答卷量化每个知识点掌握度' },
  { short: '检索', title: '🔍 RAG 检索资源…', desc: 'bge-m3 向量召回候选学习资源' },
  { short: '规划', title: '🗺️ 规划 Agent 编排路径…', desc: '结合先修关系与时间预算生成路径' },
  { short: '评价', title: '📊 评价 Agent 打分…', desc: '五维客观评分:针对性/顺序/可行性/个性化/资源' },
]

function startLoadingTimers() {
  loadingStage.value = 0
  elapsed.value = 0
  // 阶段切换:大致按经验耗时切(诊断 8s, 检索 2s, 规划 12s, 评价 直到结束)
  const breaks = [8, 10, 22] // 累计秒数
  const t0 = Date.now()
  elapsedTimer = setInterval(() => {
    elapsed.value = Math.round((Date.now() - t0) / 1000)
  }, 200)
  stageTimer = setInterval(() => {
    const sec = (Date.now() - t0) / 1000
    if (sec < breaks[0]) loadingStage.value = 0
    else if (sec < breaks[1]) loadingStage.value = 1
    else if (sec < breaks[2]) loadingStage.value = 2
    else loadingStage.value = 3
  }, 500)
}

function stopLoadingTimers() {
  if (stageTimer) clearInterval(stageTimer); stageTimer = null
  if (elapsedTimer) clearInterval(elapsedTimer); elapsedTimer = null
}

const currentQuestion = computed(() => diagnoseStore.questions[currentIndex.value] || diagnoseStore.questions[0])

const answeredCount = computed(() => Object.keys(diagnoseStore.answers).length)

const unansweredCount = computed(() =>
  Math.max(0, diagnoseStore.questions.length - answeredCount.value)
)

const progressPercent = computed(() => {
  const total = diagnoseStore.questions.length
  if (!total) return 0
  return Math.round((answeredCount.value / total) * 100)
})

const sortedMastery = computed(() => {
  return Object.fromEntries(
    Object.entries(diagnoseStore.mastery).sort((a, b) => (a[1] ?? 0) - (b[1] ?? 0))
  )
})

function normalizeChoices(raw: any) {
  if (!raw) return []
  if (Array.isArray(raw)) {
    return raw.map((text, i) => ({ key: String.fromCharCode(65 + i), text: String(text ?? '') }))
  }
  if (typeof raw === 'object') {
    return Object.entries(raw).map(([key, text]) => ({ key, text: String(text ?? '') }))
  }
  return []
}

function selectAnswer(qid: number, answer: string) {
  diagnoseStore.startTimer(qid)
  diagnoseStore.setAnswer(qid, answer)
}

function goTo(i: number) {
  currentIndex.value = i
  if (currentQuestion.value) diagnoseStore.startTimer(currentQuestion.value.id)
}

function prevQuestion() { if (currentIndex.value > 0) goTo(currentIndex.value - 1) }
function nextQuestion() { if (currentIndex.value < diagnoseStore.questions.length - 1) goTo(currentIndex.value + 1) }

async function reload() {
  loading.value = true
  try {
    await diagnoseStore.fetchQuestions(qCount.value)
    currentIndex.value = 0
  } catch {
    ElMessage.error('加载题目失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

async function confirmIfHasAnswers(action: string): Promise<boolean> {
  if (answeredCount.value === 0) return true
  try {
    await ElMessageBox.confirm(
      `当前已答 ${answeredCount.value} 题,${action}会清空作答记录,确定吗?`,
      '确认',
      { type: 'warning', confirmButtonText: '继续', cancelButtonText: '取消' },
    )
    return true
  } catch {
    return false
  }
}

async function onQCountChange(v: number | string) {
  if (await confirmIfHasAnswers('切换题数')) {
    qCount.value = Number(v)
    await reload()
  }
}

async function onReloadClick() {
  if (await confirmIfHasAnswers('重新抽题')) {
    await reload()
  }
}

async function submitDiagnose() {
  const unanswered = diagnoseStore.questions.length - answeredCount.value
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

  startLoadingTimers()
  try {
    const res = await diagnoseStore.submitDiagnose(sid)
    pathStore.setPath(res.path)
    assessStore.setFromDiagnose(res.mastery, res.path, res.reasoning, res.mock, res.evaluation)
    ElMessage.success('诊断完成！')
    await nextTick()
    renderRadar()
  } catch {
    // ECONNABORTED / 网络错误:api 拦截器已弹 message,这里不重复
  } finally {
    stopLoadingTimers()
  }
}

async function restartDiagnose() {
  try {
    await ElMessageBox.confirm('重新诊断会清空当前结果，继续吗？', '确认', { type: 'warning' })
  } catch { return }
  diagnoseStore.reset()
  await reload()
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
  // 修复:模块未涉及时返回 null(echarts 会断线显示),避免误导为 0%
  const avgValues = modules.map(m => {
    const arr = categories[m]
    if (!arr.length) return null as unknown as number
    return Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 100)
  })
  const untouched = modules.filter((m, i) => avgValues[i] == null)
  chart.setOption({
    tooltip: {
      formatter: (p: any) => {
        const lines = modules.map((m, i) => {
          const v = p.value[i]
          return `${m}: ${v == null ? '未测试' : v + '%'}`
        })
        return lines.join('<br/>')
      }
    },
    radar: {
      indicator: modules.map(m => ({ name: m, max: 100 })),
      shape: 'polygon',
      splitNumber: 5,
      // 未涉及模块名加灰色提示
      axisName: {
        formatter: (name: string) => untouched.includes(name) ? `${name} (未测试)` : name,
        color: (name: string) => untouched.includes(name) ? '#c0c4cc' : '#606266',
      } as any,
    },
    series: [{
      type: 'radar',
      data: [{
        value: avgValues, name: '平均掌握度',
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
  if (diagnoseStore.questions.length === 0 && !diagnoseStore.isSubmitted) {
    await reload()
  }
  if (diagnoseStore.isSubmitted) {
    await nextTick()
    renderRadar()
  }
})

watch(() => diagnoseStore.isSubmitted, (val) => {
  if (val) nextTick(() => renderRadar())
})
</script>

<style scoped>
.config-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
}
.config-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.config-label {
  font-size: 13px;
  color: #606266;
}
.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #606266;
}
.question-card {
  min-height: 320px;
}
.question-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.difficulty { font-size: 12px; }
.sufficient-hint { margin-bottom: 16px; }
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
  min-width: 22px;
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
.sheet-item:hover {
  border-color: #409eff;
}
.sheet-item.answered {
  background: #67c23a;
  color: #fff;
  border-color: #67c23a;
}
.sheet-item.unanswered {
  background: #fff;
  color: #909399;
  border-color: #e4e7ed;
  border-style: dashed;
}
.sheet-item.current {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64,158,255,0.2);
}
.sheet-legend {
  display: inline-flex;
  gap: 14px;
  margin-left: 16px;
  font-size: 12px;
  font-weight: 400;
  color: #909399;
}
.sheet-legend .legend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.sheet-legend .ld {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}
.sheet-legend .ld-done { background: #67c23a; }
.sheet-legend .ld-todo { background: #fff; border: 1px dashed #c0c4cc; }
.sheet-legend .ld-cur { background: #fff; border: 2px solid #409eff; }
.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.sub-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}
.agent-text {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 14px;
  max-height: 320px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.8;
  color: #606266;
}
.reason-line {
  padding: 2px 0;
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
  width: 200px;
  font-size: 13px;
  text-align: right;
  flex-shrink: 0;
}
.rotate {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}
.diagnose-loading-mask {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.loading-card {
  background: #fff;
  padding: 32px 44px;
  border-radius: 12px;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.12);
  text-align: center;
  min-width: 420px;
}
.loading-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-top: 14px;
}
.loading-desc {
  font-size: 13px;
  color: #606266;
  margin-top: 8px;
  line-height: 1.6;
}
.loading-progress {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-top: 24px;
  padding: 0 8px;
  position: relative;
}
.loading-progress::before {
  content: '';
  position: absolute;
  top: 13px;
  left: 22px;
  right: 22px;
  height: 2px;
  background: #e4e7ed;
  z-index: 0;
}
.stage-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  position: relative;
  z-index: 1;
  background: #fff;
  padding: 0 6px;
}
.stage-dot .dot-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e4e7ed;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
}
.stage-dot .dot-label {
  font-size: 12px;
  color: #909399;
}
.stage-dot.active .dot-num {
  background: #409eff;
  color: #fff;
  animation: pulse 1.2s ease-in-out infinite;
}
.stage-dot.active .dot-label {
  color: #409eff;
  font-weight: 600;
}
.stage-dot.done .dot-num {
  background: #67c23a;
  color: #fff;
}
.stage-dot.done .dot-label {
  color: #67c23a;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(64, 158, 255, 0); }
}
.loading-elapsed {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 18px;
  font-family: 'SF Mono', ui-monospace, monospace;
}
</style>
