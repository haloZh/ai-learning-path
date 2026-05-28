<template>
  <div class="page-container">
    <h2 class="page-title">🗺️ 学习路径</h2>

    <div class="card">
      <el-tabs v-model="activeView">
        <el-tab-pane label="路径列表" name="timeline" />
        <el-tab-pane label="知识图谱视图" name="graph" />
      </el-tabs>
      <el-tag v-if="pathStore.isMock" type="warning" size="small">⚠️ Mock</el-tag>
      <el-tag v-else-if="pathStore.pathData.length > 0" type="success" size="small">✓ LLM</el-tag>
    </div>

    <div v-if="activeView === 'timeline'">
      <div v-if="pathStore.pathData.length === 0" class="card" style="text-align:center;padding:40px">
        <p style="color:#909399">暂无学习路径，请先完成诊断测验</p>
        <el-button type="primary" @click="$router.push('/diagnose')" style="margin-top:12px">去诊断 →</el-button>
      </div>

      <div v-for="(item, idx) in pathStore.pathData" :key="idx" class="card">
        <div class="path-item">
          <div class="path-item-header">
            <span class="path-index">#{{ idx + 1 }}</span>
            <span class="path-concept">{{ item.concept_id }}</span>
            <el-tag size="small" type="info">{{ item.estimated_minutes }} 分钟</el-tag>
          </div>
          <div class="path-title">{{ item.title }}</div>
          <ExplainCard v-if="item.reason" :reasons="[item.reason]" />
        </div>
      </div>

      <div v-if="pathStore.pathData.length > 0" class="card path-stats">
        <el-row :gutter="24">
          <el-col :span="8">
            <el-statistic title="学习项数" :value="pathStore.pathData.length" suffix="项" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="预计总时长" :value="totalMinutes" suffix="分钟" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="知识点覆盖" :value="pathStore.pathData.length" suffix="个" />
          </el-col>
        </el-row>
      </div>
    </div>

    <div v-if="activeView === 'graph'" class="card">
      <div ref="graphRef" style="width:100%;height:500px"></div>
      <div class="graph-legend">
        <span>🟢 已掌握(≥70%)</span>
        <span>🟡 薄弱(30-70%)</span>
        <span>🔴 极弱(&lt;30%)</span>
        <span>⚪ 未学</span>
      </div>
    </div>

    <div v-if="pathStore.pathData.length > 0" class="card" style="text-align:center">
      <el-button type="primary" size="large" @click="$router.push('/learn')">开始学习 →</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { usePathStore, useStudentStore, useDiagnoseStore } from '@/stores'
import ExplainCard from '@/components/ExplainCard.vue'

const pathStore = usePathStore()
const studentStore = useStudentStore()
const diagnoseStore = useDiagnoseStore()
const activeView = ref('timeline')
const graphRef = ref<HTMLElement>()

const totalMinutes = computed(() => pathStore.pathData.reduce((s, i) => s + i.estimated_minutes, 0))

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
  const catColors: Record<string, string> = { '算术': '#67c23a', '代数': '#409eff', '几何': '#e6a23c', '数据分析': '#f56c6c' }

  function getGroup(code: string) {
    if (code.startsWith('算术')) return '算术'
    if (code.startsWith('代数')) return '代数'
    if (code.startsWith('几何')) return '几何'
    return '数据分析'
  }

  const nodes = concepts.map(c => {
    const m = mastery[c.code] ?? -1
    let color = '#c0c4cc'
    if (m >= 0.7) color = '#67c23a'
    else if (m >= 0.3) color = '#e6a23c'
    else if (m > 0) color = '#f56c6c'
    const group = getGroup(c.code)
    return {
      id: c.code,
      name: c.name,
      symbolSize: m >= 0 ? 25 + m * 25 : 20,
      itemStyle: { color },
      category: categories.indexOf(group),
      label: { show: true, fontSize: 10 }
    }
  })

  const links = concepts.flatMap(c =>
    (c.prerequisite_codes || []).map(pre => ({ source: pre, target: c.code }))
  )

  chart.setOption({
    tooltip: {},
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
      try {
        await pathStore.fetchPath(sid)
      } catch {}
    }
    if (pathStore.concepts.length === 0) {
      try {
        await pathStore.fetchConcepts('管综数学')
      } catch {}
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
.path-item {
  padding: 4px 0;
}
.path-item-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.path-index {
  background: #409eff;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}
.path-concept {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}
.path-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}
.path-stats {
  text-align: center;
}
.graph-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 12px;
  font-size: 13px;
  color: #606266;
}
</style>
