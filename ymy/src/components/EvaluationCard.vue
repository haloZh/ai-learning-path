<template>
  <div class="evaluation-card">
    <div class="eval-head">
      <span class="eval-title">📊 路径质量评分</span>
      <span class="eval-score" :class="scoreClass(evaluation.score)">
        {{ evaluation.score }}<small>/100</small>
      </span>
    </div>
    <div class="eval-grid">
      <div v-for="(label, key) in EVAL_KEYS" :key="key" class="eval-item">
        <span class="eval-label">{{ label }}</span>
        <span class="eval-bar">
          <span
            :style="{ width: ((scoreOf(key)) * 10) + '%' }"
            :class="scoreSubClass(scoreOf(key))"
          ></span>
        </span>
        <span class="eval-num">{{ scoreOf(key) || '-' }}</span>
      </div>
    </div>
    <div v-if="hasDetail" class="eval-toggle" @click="expanded = !expanded">
      <span>{{ expanded ? '▲ 收起详细评语' : '▼ 展开亮点 / 待改进 / 总评' }}</span>
    </div>
    <transition name="slide-fade">
      <div v-show="expanded && hasDetail" class="eval-detail">
        <div v-if="evaluation.summary" class="eval-summary">📝 {{ evaluation.summary }}</div>
        <div v-if="evaluation.strengths" class="eval-line eval-strength">
          <b>亮点:</b> {{ evaluation.strengths }}
        </div>
        <div v-if="evaluation.improvements" class="eval-line eval-improve">
          <b>待改进:</b> {{ evaluation.improvements }}
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Evaluation } from '@/types'

const props = defineProps<{ evaluation: Evaluation }>()

const expanded = ref(false)

const hasDetail = computed(
  () => !!(props.evaluation.summary || props.evaluation.strengths || props.evaluation.improvements)
)

const EVAL_KEYS: Record<string, string> = {
  targeting: '针对性',
  ordering: '顺序合理性',
  feasibility: '可行性',
  personalization: '个性化',
  resource_match: '资源匹配',
}

function scoreOf(key: string): number {
  return (props.evaluation.scores as any)?.[key] ?? 0
}

function scoreClass(score: number) {
  if (score >= 80) return 'score-high'
  if (score >= 60) return 'score-mid'
  return 'score-low'
}

function scoreSubClass(v: number) {
  if (v >= 8) return 'high'
  if (v >= 5) return 'mid'
  return 'low'
}
</script>

<style scoped>
.evaluation-card {
  background: linear-gradient(135deg, #fff8e1 0%, #fff3e0 100%);
  border: 1px solid #ffe0b2;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
}
.eval-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}
.eval-title {
  font-size: 16px;
  font-weight: 600;
  color: #e65100;
}
.eval-score {
  font-size: 32px;
  font-weight: 700;
  font-family: 'SF Mono', ui-monospace, monospace;
}
.eval-score small {
  font-size: 14px;
  font-weight: 400;
  color: #888;
}
.score-high { color: #2e7d32; }
.score-mid  { color: #f57c00; }
.score-low  { color: #c62828; }
.eval-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px 24px;
  margin-bottom: 8px;
}
.eval-item {
  display: grid;
  grid-template-columns: 90px 1fr 30px;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.eval-label { color: #555; }
.eval-bar {
  background: rgba(0, 0, 0, 0.06);
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
}
.eval-bar > span {
  display: block;
  height: 100%;
  transition: width 0.5s ease;
}
.eval-bar > .low  { background: #ef5350; }
.eval-bar > .mid  { background: #ffb300; }
.eval-bar > .high { background: #66bb6a; }
.eval-num {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 12px;
  color: #666;
  text-align: right;
}
.eval-toggle {
  margin-top: 10px;
  text-align: center;
  font-size: 12px;
  color: #e65100;
  cursor: pointer;
  user-select: none;
  padding: 6px;
  border-radius: 6px;
  transition: background 0.2s;
}
.eval-toggle:hover {
  background: rgba(255, 152, 0, 0.08);
}
.eval-detail {
  margin-top: 4px;
}
.eval-summary {
  font-size: 13px;
  color: #444;
  margin-top: 4px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 6px;
}
.eval-line {
  font-size: 13px;
  color: #555;
  margin-top: 8px;
  line-height: 1.6;
}
.eval-line b { color: #e65100; }
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
  max-height: 0;
}
</style>
