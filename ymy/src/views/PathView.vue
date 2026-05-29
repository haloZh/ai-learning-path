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
          <el-tab-pane label="📋 路径列表" name="timeline" />
          <el-tab-pane label="🕸 知识图谱" name="graph" />
        </el-tabs>
        <div class="status-tags">
          <el-tag v-if="pathStore.isMock" type="warning" size="small">⚠️ Mock 兜底</el-tag>
          <el-tag v-else type="success" size="small">✓ LLM 真实输出</el-tag>
        </div>
      </div>

      <EvaluationCard v-if="diagnoseStore.evaluation" :evaluation="diagnoseStore.evaluation" />

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
import { ref, computed, onMounted, nextTick, watch } from 'vue'
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
const activeView = ref('timeline')
const graphRef = ref<HTMLElement>()

const totalMinutes = computed(() => pathStore.pathData.reduce((s, i) => s + (i.estimated_minutes || 0), 0))
const avgMinutes = computed(() => {
  const n = pathStore.pathData.length
  if (!n) return 0
  return Math.round(totalMinutes.value / n)
})

function renderGraph() {
  if (!graphRef.value) return
  const chart = echarts.init(graphRef.value)
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
</script>

<style scoped>
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
