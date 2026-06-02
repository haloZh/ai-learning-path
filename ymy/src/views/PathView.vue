<template>
  <div class="page-container">
    <h2 class="page-title">🗺️ 学习路径</h2>

    <div v-if="pathStore.pathData.length === 0" class="card" style="text-align:center;padding:40px">
      <p style="color:#909399">暂无学习路径，请先完成诊断测验</p>
      <el-button type="primary" @click="$router.push('/diagnose')" style="margin-top:12px">去诊断 →</el-button>
    </div>

    <template v-else>
      <div class="card status-bar">
        <el-tabs v-model="activeView" style="flex:1">
          <el-tab-pane label="🎯 闯关路线" name="roadmap" />
          <el-tab-pane label="📋 路径列表" name="timeline" />
          <el-tab-pane label="🕸 知识图谱" name="graph" />
        </el-tabs>
        <div class="status-tags">
          <el-tag v-if="pathStore.isMock" type="warning" size="small">⚠️ Mock 兜底</el-tag>
          <el-tag v-else type="success" size="small">✓ LLM 真实输出</el-tag>
        </div>
      </div>

      <!-- 闯关路线图:节点串成路径,直观展示学习程度 -->
      <div v-if="activeView === 'roadmap'">
        <div class="card roadmap-progress">
          <div class="rp-head">
            <span class="rp-title">学习进度</span>
            <span class="rp-count">{{ completedCount }} / {{ pathStore.pathData.length }} 项 ({{ progressPercent }}%)</span>
          </div>
          <el-progress
            :percentage="progressPercent"
            :stroke-width="16"
            :status="progressPercent === 100 ? 'success' : ''"
          />
          <div class="rp-meta">
            <span>✅ 已完成 {{ completedCount }} 项</span>
            <span>⏱ 累计学习 {{ learnedMinutes }} 分钟</span>
            <span>📍 剩余 {{ pathStore.pathData.length - completedCount }} 项</span>
          </div>
        </div>

        <div class="card roadmap-card">
          <div class="card-title">🎯 闯关路线（点击节点开始学习）</div>
          <div class="roadmap">
            <div
              v-for="(item, idx) in pathStore.pathData" :key="idx"
              class="rm-node"
              :class="nodeStatus(idx)"
              @click="goToLearn(idx)"
            >
              <div class="rm-connector" v-if="idx > 0" :class="{ done: isDone(idx - 1) }"></div>
              <div class="rm-circle">
                <span v-if="isDone(idx)" class="rm-icon">✓</span>
                <span v-else-if="nodeStatus(idx) === 'current'" class="rm-icon">▶</span>
                <span v-else>{{ idx + 1 }}</span>
              </div>
              <div class="rm-body">
                <div class="rm-title">{{ item.title }}</div>
                <div class="rm-sub">
                  <el-tag size="small" :type="statusTagType(idx)" effect="plain">{{ statusLabel(idx) }}</el-tag>
                  <span class="rm-concept">🏷 {{ item.concept_id }}</span>
                  <span class="rm-min">⏱ {{ item.estimated_minutes }}分钟</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <EvaluationCard v-if="diagnoseStore.evaluation && activeView !== 'roadmap'" :evaluation="diagnoseStore.evaluation" />

      <div v-if="activeView === 'timeline'">
        <div class="card timeline-card">
          <div class="card-title">🛤️ 推荐学习时序</div>
          <div class="timeline">
            <div
              v-for="(item, idx) in pathStore.pathData" :key="idx"
              class="timeline-item"
              @click="goToLearn(idx)"
            >
              <div class="timeline-dot">{{ idx + 1 }}</div>
              <div class="timeline-line" v-if="idx < pathStore.pathData.length - 1"></div>
              <div class="timeline-content clickable">
                <div class="timeline-head">
                  <span class="timeline-title">{{ item.title }}</span>
                  <el-tag size="small" type="info">⏱ {{ item.estimated_minutes }} 分钟</el-tag>
                  <el-tag size="small">🏷 {{ item.concept_id }}</el-tag>
                  <span class="timeline-cta">开始学习 →</span>
                </div>
                <div v-if="item.reason" class="timeline-reason">💡 {{ item.reason }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="card path-stats">
          <el-row :gutter="24">
            <el-col :span="8">
              <el-statistic title="学习项数" :value="pathStore.pathData.length" suffix="项" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="预计总时长" :value="totalMinutes" suffix="分钟" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="平均单项耗时" :value="avgMinutes" suffix="分钟" />
            </el-col>
          </el-row>
        </div>
      </div>

      <div v-if="activeView === 'graph'" class="card">
        <div ref="graphRef" style="width:100%;height:500px"></div>
        <div class="graph-legend">
          <span class="legend-item"><span class="dot dot-success"></span> 已掌握 (≥70%)</span>
          <span class="legend-item"><span class="dot dot-warning"></span> 薄弱 (30-70%)</span>
          <span class="legend-item"><span class="dot dot-danger"></span> 极弱 (&lt;30%)</span>
          <span class="legend-item"><span class="dot dot-unknown"></span> 未涉及（虚线）</span>
        </div>
      </div>

      <div class="card action-bar">
        <el-button @click="$router.push('/diagnose')">← 返回诊断</el-button>
        <el-button type="primary" size="large" @click="$router.push('/learn')">开始学习 →</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { usePathStore, useStudentStore, useDiagnoseStore, useLearnStore } from '@/stores'
import EvaluationCard from '@/components/EvaluationCard.vue'

const router = useRouter()
const pathStore = usePathStore()
const studentStore = useStudentStore()
const diagnoseStore = useDiagnoseStore()
const learnStore = useLearnStore()

function goToLearn(idx: number) {
  if (learnStore.currentPath.length === 0) {
    learnStore.setCurrentPath(pathStore.pathData)
  }
  learnStore.setInitialIdx(idx)
  router.push('/learn')
}
const activeView = ref('roadmap')
const graphRef = ref<HTMLElement>()
let graphChart: echarts.ECharts | null = null

const totalMinutes = computed(() => pathStore.pathData.reduce((s, i) => s + (i.estimated_minutes || 0), 0))
const avgMinutes = computed(() => {
  const n = pathStore.pathData.length
  if (!n) return 0
  return Math.round(totalMinutes.value / n)
})

// ===== 闯关路线进度(依据学习工作台的完成标记) =====
const itemKey = (i: number) => {
  const it = pathStore.pathData[i]
  return it ? `${it.concept_id}::${it.title}` : ''
}
function isDone(idx: number): boolean {
  return learnStore.isCompleted(itemKey(idx))
}
const completedCount = computed(() =>
  pathStore.pathData.filter((_, i) => isDone(i)).length
)
const progressPercent = computed(() => {
  const n = pathStore.pathData.length
  return n ? Math.round((completedCount.value / n) * 100) : 0
})
const learnedMinutes = computed(() =>
  pathStore.pathData.reduce((s, it, i) => s + (isDone(i) ? (it.estimated_minutes || 0) : 0), 0)
)
// 当前节点 = 第一个未完成的节点
const currentNodeIdx = computed(() => {
  const idx = pathStore.pathData.findIndex((_, i) => !isDone(i))
  return idx === -1 ? -1 : idx // -1 表示全部完成
})
function nodeStatus(idx: number): 'done' | 'current' | 'todo' {
  if (isDone(idx)) return 'done'
  if (idx === currentNodeIdx.value) return 'current'
  return 'todo'
}
function statusLabel(idx: number): string {
  return { done: '已完成', current: '学习中', todo: '未开始' }[nodeStatus(idx)]
}
function statusTagType(idx: number): 'success' | 'warning' | 'info' {
  return ({ done: 'success', current: 'warning', todo: 'info' } as const)[nodeStatus(idx)]
}

function renderGraph() {
  if (!graphRef.value) return
  if (!graphChart) {
    graphChart = echarts.init(graphRef.value)
  } else {
    graphChart.clear()
  }
  const chart = graphChart
  const concepts = pathStore.concepts
  const mastery = diagnoseStore.mastery

  if (concepts.length === 0) {
    chart.setOption({
      title: { text: '暂无知识图谱数据', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 16 } }
    })
    return
  }

  const categories = ['算术', '代数', '几何', '数据分析']

  function getGroup(code: string) {
    if (code.startsWith('算术')) return '算术'
    if (code.startsWith('代数')) return '代数'
    if (code.startsWith('几何')) return '几何'
    return '数据分析'
  }

  const nodes = concepts.map(c => {
    const m = mastery[c.code]
    const isUnknown = m == null
    let color = '#c0c4cc'
    if (!isUnknown) {
      if (m >= 0.7) color = '#67c23a'
      else if (m >= 0.3) color = '#e6a23c'
      else color = '#f56c6c'
    }
    const group = getGroup(c.code)
    return {
      id: c.code,
      name: c.name,
      symbolSize: !isUnknown ? 25 + m * 25 : 18,
      itemStyle: {
        color,
        borderColor: isUnknown ? '#c0c4cc' : color,
        borderWidth: isUnknown ? 2 : 0,
        borderType: isUnknown ? 'dashed' : 'solid',
        opacity: isUnknown ? 0.65 : 1,
      },
      category: categories.indexOf(group),
      label: { show: true, fontSize: 10 }
    }
  })

  const links = concepts.flatMap(c =>
    (c.prerequisite_codes || []).map(pre => ({ source: pre, target: c.code }))
  )

  chart.setOption({
    tooltip: {
      formatter: (p: any) => {
        if (p.dataType !== 'node') return ''
        const m = mastery[p.data.id]
        if (m == null) return `${p.name}<br/>未涉及`
        return `${p.name}<br/>掌握度: ${(m * 100).toFixed(0)}%`
      }
    },
    legend: { data: categories, bottom: 0 },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links,
      categories: categories.map(c => ({ name: c })),
      roam: true,
      draggable: true,
      force: { repulsion: 200, edgeLength: 120 },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: 8,
      label: { show: true, position: 'bottom' },
      lineStyle: { color: '#aaa', curveness: 0.1 }
    }]
  })
}

onMounted(async () => {
  const sid = studentStore.studentId
  if (sid) {
    if (!pathStore.isPathGenerated) {
      try { await pathStore.fetchPath(sid) } catch {}
    }
    if (pathStore.concepts.length === 0) {
      try { await pathStore.fetchConcepts('管综数学') } catch {}
    }
  }
  nextTick(() => {
    if (activeView.value === 'graph') renderGraph()
  })
})

watch(activeView, (v) => {
  if (v === 'graph') nextTick(() => renderGraph())
})

function onResize() { graphChart?.resize() }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  graphChart?.dispose()
  graphChart = null
})
</script>

<style scoped>
/* ===== 闯关路线图 ===== */
.roadmap-progress {
  padding: 18px 24px;
}
.rp-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.rp-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.rp-count {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}
.rp-meta {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  font-size: 13px;
  color: #606266;
}
.roadmap-card {
  padding: 20px 28px;
}
.roadmap {
  display: flex;
  flex-direction: column;
}
.rm-node {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
  cursor: pointer;
  transition: transform 0.2s;
}
.rm-node:hover {
  transform: translateX(4px);
}
/* 节点之间的连接线 */
.rm-connector {
  position: absolute;
  left: 21px;
  top: -16px;
  width: 2px;
  height: 24px;
  background: #e4e7ed;
}
.rm-connector.done {
  background: #67c23a;
}
.rm-circle {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  border: 2px solid #dcdfe6;
  background: #fff;
  color: #909399;
  z-index: 1;
  transition: all 0.3s;
}
.rm-node.done .rm-circle {
  background: #67c23a;
  border-color: #67c23a;
  color: #fff;
}
.rm-node.current .rm-circle {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
  animation: rm-pulse 1.4s ease-in-out infinite;
}
.rm-node.todo .rm-circle {
  background: #fff;
  border-color: #dcdfe6;
  color: #c0c4cc;
}
@keyframes rm-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.45); }
  50% { box-shadow: 0 0 0 8px rgba(64, 158, 255, 0); }
}
.rm-icon {
  font-size: 18px;
  line-height: 1;
}
.rm-body {
  flex: 1;
}
.rm-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.rm-node.todo .rm-title {
  color: #909399;
}
.rm-node.done .rm-title {
  color: #67c23a;
}
.rm-sub {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 24px;
}
.status-bar :deep(.el-tabs__nav-wrap::after) {
  display: none;
}
.status-bar :deep(.el-tabs__header) {
  margin: 0;
}
.status-tags {
  flex-shrink: 0;
}
.timeline-card {
  padding-left: 28px;
}
.timeline {
  position: relative;
  padding: 8px 0 8px 36px;
}
.timeline-item {
  position: relative;
  padding-bottom: 24px;
}
.timeline-item:last-child { padding-bottom: 0; }
.timeline-dot {
  position: absolute;
  left: -36px;
  top: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  z-index: 2;
}
.timeline-line {
  position: absolute;
  left: -23px;
  top: 28px;
  bottom: -4px;
  width: 2px;
  background: #e4e7ed;
}
.timeline-content {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  padding: 14px 16px;
  transition: all 0.2s;
}
.timeline-content.clickable {
  cursor: pointer;
}
.timeline-content.clickable:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
  transform: translateX(2px);
}
.timeline-content.clickable:hover .timeline-cta {
  opacity: 1;
}
.timeline-cta {
  margin-left: auto;
  font-size: 12px;
  color: #409eff;
  font-weight: 500;
  opacity: 0;
  transition: opacity 0.2s;
}
.timeline-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}
.timeline-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.timeline-reason {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  padding-top: 4px;
}
.path-stats {
  text-align: center;
}
.graph-legend {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 12px;
  font-size: 13px;
  color: #606266;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}
.dot-success { background: #67c23a; }
.dot-warning { background: #e6a23c; }
.dot-danger { background: #f56c6c; }
.dot-unknown { background: transparent; border: 2px dashed #c0c4cc; }
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
