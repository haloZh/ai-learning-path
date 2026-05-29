<template>
  <div class="page-container">
    <h2 class="page-title">📊 评估看板</h2>

    <div v-if="!assessStore.isLoaded" class="card" style="text-align:center;padding:40px">
      <p style="color:#909399">暂无评估数据，请先完成诊断测验</p>
      <el-button type="primary" @click="$router.push('/diagnose')" style="margin-top:12px">去诊断 →</el-button>
    </div>

    <template v-else>
      <!-- 评价卡片(LLM 五维评分) -->
      <EvaluationCard v-if="assessStore.evaluation" :evaluation="assessStore.evaluation" />

      <!-- 概览统计 -->
      <div class="card">
        <div class="card-title">
          学习概览
          <el-tag v-if="assessStore.isMock" type="warning" size="small" style="margin-left:8px">⚠️ Mock</el-tag>
          <el-tag v-else type="success" size="small" style="margin-left:8px">✓ LLM</el-tag>
        </div>
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-value">{{ assessStore.path.length }}</div>
            <div class="metric-label">学习路径项</div>
          </div>
          <div class="metric-card highlight">
            <div class="metric-value">{{ weakCount }}</div>
            <div class="metric-label">薄弱知识点</div>
          </div>
          <div class="metric-card success">
            <div class="metric-value">{{ masteredCount }}</div>
            <div class="metric-label">已掌握知识点</div>
          </div>
          <div class="metric-card neutral">
            <div class="metric-value">{{ untouchedCount }}</div>
            <div class="metric-label">未涉及知识点</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{{ totalMinutes }}</div>
            <div class="metric-label">预计总时长(分钟)</div>
          </div>
        </div>
      </div>

      <!-- 掌握度分布 + 推理日志 -->
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="card">
            <div class="card-title">📈 掌握度分布</div>
            <div ref="masteryChartRef" style="width:100%;height:350px"></div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <div class="card-title">🧠 Agent 推理日志</div>
            <div class="reasoning-list">
              <div v-for="(r, i) in assessStore.reasoning" :key="i" class="reasoning-item">
                <el-tag size="small" :type="reasonTagType(r)" effect="plain">
                  {{ reasonLabel(r) }}
                </el-tag>
                <span class="reasoning-text">{{ stripPrefix(r) }}</span>
              </div>
              <div v-if="assessStore.reasoning.length === 0" style="color:#909399;text-align:center;padding:20px">
                暂无推理日志
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 学习路径表格 -->
      <div class="card">
        <div class="card-title">🗺️ 学习路径明细</div>
        <el-table :data="assessStore.path" stripe size="small" :header-cell-style="{ background: '#f5f7fa' }">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="concept_id" label="知识点" width="180" show-overflow-tooltip />
          <el-table-column prop="title" label="学习内容" min-width="200" show-overflow-tooltip />
          <el-table-column prop="estimated_minutes" label="时长" width="80" align="center">
            <template #default="{ row }">{{ row.estimated_minutes }} min</template>
          </el-table-column>
          <el-table-column prop="reason" label="推荐理由" min-width="240" show-overflow-tooltip />
        </el-table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { useAssessStore, usePathStore } from '@/stores'
import EvaluationCard from '@/components/EvaluationCard.vue'

const assessStore = useAssessStore()
const pathStore = usePathStore()
const masteryChartRef = ref<HTMLElement>()

const weakCount = computed(() => Object.values(assessStore.mastery).filter(v => v < 0.3).length)
const masteredCount = computed(() => Object.values(assessStore.mastery).filter(v => v >= 0.7).length)
// 未涉及:有 path 但 mastery 里没出现的,或显式为 0 的
const untouchedCount = computed(() => Object.values(assessStore.mastery).filter(v => v === 0).length)
const totalMinutes = computed(() => assessStore.path.reduce((s, i) => s + (i.estimated_minutes || 0), 0))

function masteryColor(v: number) {
  if (v >= 0.7) return '#67c23a'
  if (v >= 0.3) return '#e6a23c'
  return '#f56c6c'
}

function reasonLabel(r: string): string {
  if (r.startsWith('[diagnose]')) return '诊断'
  if (r.startsWith('[plan]')) return '规划'
  if (r.startsWith('[evaluate]')) return '评价'
  if (r.startsWith('[optimize]') || r.startsWith('[interaction]')) return '优化'
  return '其他'
}

function reasonTagType(r: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  if (r.startsWith('[diagnose]')) return 'primary'
  if (r.startsWith('[plan]')) return 'success'
  if (r.startsWith('[evaluate]')) return 'warning'
  if (r.startsWith('[optimize]') || r.startsWith('[interaction]')) return 'danger'
  return 'info'
}

function stripPrefix(r: string): string {
  return r.replace(/^\[[a-z]+\]\s*/i, '')
}

function renderMasteryChart() {
  if (!masteryChartRef.value) return
  const chart = echarts.init(masteryChartRef.value)
  // 已诊断的(按掌握度升序) + 未涉及的(灰色,放最末)
  const tested = Object.entries(assessStore.mastery).sort((a, b) => a[1] - b[1])
  const testedKeys = new Set(tested.map(([k]) => k))
  const untouched = pathStore.concepts
    .map(c => c.code)
    .filter(code => !testedKeys.has(code))

  const all: Array<{ name: string; value: number; color: string; isUnknown: boolean }> = []
  for (const [k, v] of tested) {
    all.push({
      name: k.split('-').pop() || k,
      value: Math.round(v * 100),
      color: masteryColor(v),
      isUnknown: false,
    })
  }
  for (const code of untouched) {
    all.push({
      name: code.split('-').pop() || code,
      value: 0,
      color: '#e4e7ed',
      isUnknown: true,
    })
  }

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (p: any) => {
        const item = p[0]
        const data = all[item.dataIndex]
        return data.isUnknown
          ? `${item.name}: 未涉及`
          : `${item.name}: ${item.value}%`
      },
    },
    grid: { top: 10, right: 60, bottom: 30, left: 110 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: (v: number) => v + '%' } },
    yAxis: { type: 'category', data: all.map(d => d.name), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: all.map(d => ({
        value: d.isUnknown ? 5 : d.value, // 未涉及给个细条占位
        itemStyle: {
          color: d.color,
          opacity: d.isUnknown ? 0.4 : 1,
        },
      })),
      barWidth: 14,
      label: {
        show: true,
        position: 'right',
        formatter: (p: any) => all[p.dataIndex].isUnknown ? '未测' : (p.value + '%'),
        color: (p: any) => all[p.dataIndex].isUnknown ? '#909399' : '#606266',
      } as any,
    }],
  })
}

onMounted(async () => {
  // 拉 concepts 用于"未涉及"展示
  if (pathStore.concepts.length === 0) {
    try { await pathStore.fetchConcepts('管综数学') } catch {}
  }
  if (assessStore.isLoaded) {
    nextTick(() => renderMasteryChart())
  }
})

watch(() => assessStore.mastery, () => {
  if (assessStore.isLoaded) nextTick(() => renderMasteryChart())
}, { deep: true })
</script>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}
.metric-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  border: 1px solid #e4e7ed;
}
.metric-card.success {
  background: #f0f9eb;
  border-color: #c2e7b0;
}
.metric-card.highlight {
  background: #fef0f0;
  border-color: #fbc4c4;
}
.metric-card.neutral {
  background: #f4f4f5;
  border-color: #d3d4d6;
}
.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
}
.metric-card.success .metric-value { color: #67c23a; }
.metric-card.highlight .metric-value { color: #f56c6c; }
.metric-card.neutral .metric-value { color: #909399; }
.metric-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.reasoning-list {
  max-height: 350px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reasoning-item {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  align-items: flex-start;
}
.reasoning-item .el-tag {
  flex-shrink: 0;
}
.reasoning-text {
  color: #606266;
  flex: 1;
}
</style>
