<template>
  <div class="page-container">
    <h2 class="page-title">📊 评估看板</h2>

    <div v-if="!assessStore.isLoaded" class="card" style="text-align:center;padding:40px">
      <p style="color:#909399">暂无评估数据，请先完成诊断测验</p>
      <el-button type="primary" @click="$router.push('/diagnose')" style="margin-top:12px">去诊断 →</el-button>
    </div>

    <template v-else>
      <div class="card">
        <div class="card-title">
          评估概览
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
          <div class="metric-card">
            <div class="metric-value">{{ totalMinutes }}</div>
            <div class="metric-label">预计总时长(分钟)</div>
          </div>
        </div>
      </div>

      <el-row :gutter="20">
        <el-col :span="12">
          <div class="card">
            <div class="card-title">掌握度分布</div>
            <div ref="masteryChartRef" style="width:100%;height:350px"></div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <div class="card-title">推理日志</div>
            <div class="reasoning-list">
              <div v-for="(r, i) in assessStore.reasoning" :key="i" class="reasoning-item">
                <span class="reasoning-index">{{ i + 1 }}</span>
                <span class="reasoning-text">{{ r }}</span>
              </div>
              <div v-if="assessStore.reasoning.length === 0" style="color:#909399;text-align:center;padding:20px">
                暂无推理日志
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <div class="card">
        <div class="card-title">详细知识点掌握度</div>
        <div class="mastery-list">
          <div v-for="(val, key) in assessStore.mastery" :key="key" class="mastery-item">
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

      <div class="card">
        <div class="card-title">学习路径</div>
        <el-table :data="assessStore.path" stripe size="small">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="concept_id" label="知识点" width="160" />
          <el-table-column prop="title" label="学习内容" />
          <el-table-column prop="estimated_minutes" label="预计时长" width="100">
            <template #default="{ row }">{{ row.estimated_minutes }} 分钟</template>
          </el-table-column>
          <el-table-column prop="reason" label="推荐理由" />
        </el-table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useAssessStore } from '@/stores'

const assessStore = useAssessStore()
const masteryChartRef = ref<HTMLElement>()

const weakCount = computed(() => Object.values(assessStore.mastery).filter(v => v < 0.3).length)
const masteredCount = computed(() => Object.values(assessStore.mastery).filter(v => v >= 0.7).length)
const totalMinutes = computed(() => assessStore.path.reduce((s, i) => s + i.estimated_minutes, 0))

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

function renderMasteryChart() {
  if (!masteryChartRef.value) return
  const chart = echarts.init(masteryChartRef.value)
  const entries = Object.entries(assessStore.mastery).sort((a, b) => a[1] - b[1])
  const names = entries.map(([k]) => k.split('-').pop() || k)
  const values = entries.map(([, v]) => Math.round(v * 100))
  const colors = entries.map(([, v]) => masteryColor(v))

  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 10, right: 30, bottom: 40, left: 100 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: (v: number) => v + '%' } },
    yAxis: { type: 'category', data: names },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
      barWidth: 16,
      label: { show: true, position: 'right', formatter: (p: any) => p.value + '%' }
    }]
  })
}

onMounted(() => {
  if (assessStore.isLoaded) {
    nextTick(() => renderMasteryChart())
  }
})
</script>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
}
.metric-card.success .metric-value {
  color: #67c23a;
}
.metric-card.highlight .metric-value {
  color: #f56c6c;
}
.metric-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
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
  width: 160px;
  font-size: 13px;
  text-align: right;
  flex-shrink: 0;
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
}
.reasoning-index {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}
.reasoning-text {
  color: #606266;
}
</style>
