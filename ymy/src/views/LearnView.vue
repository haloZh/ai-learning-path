<template>
  <div class="page-container">
    <h2 class="page-title">📖 学习工作台</h2>

    <div v-if="learnStore.currentPath.length === 0" class="card" style="text-align:center;padding:40px">
      <p style="color:#909399">暂无学习任务，请先完成诊断测验并生成路径</p>
      <el-button type="primary" @click="$router.push('/diagnose')" style="margin-top:12px">去诊断 →</el-button>
    </div>

    <template v-else>
      <div class="card current-task">
        <div class="task-header">
          <span>📍 当前学习：{{ currentItem?.concept_id }}</span>
          <el-tag size="small">{{ currentItem?.estimated_minutes }} 分钟</el-tag>
          <el-tag v-if="learnStore.isMock" type="warning" size="small">⚠️ Mock</el-tag>
        </div>
        <div class="task-title">{{ currentItem?.title }}</div>
        <div v-if="currentItem?.reason" class="task-reason">💡 {{ currentItem.reason }}</div>
      </div>

      <el-row :gutter="20">
        <el-col :span="14">
          <div class="card">
            <div class="card-title">学习路径项</div>
            <div class="path-list">
              <div
                v-for="(item, idx) in learnStore.currentPath" :key="idx"
                class="path-item-row"
                :class="{ active: idx === currentIdx, highlight: isNewItem(item) }"
                @click="currentIdx = idx"
              >
                <span class="item-index">{{ idx + 1 }}</span>
                <div class="item-body">
                  <div class="item-concept">{{ item.concept_id }}</div>
                  <div class="item-title">{{ item.title }}</div>
                </div>
                <el-tag size="small" type="info">{{ item.estimated_minutes }}min</el-tag>
              </div>
            </div>
          </div>
        </el-col>

        <el-col :span="10">
          <div class="card">
            <div class="card-title">学习反馈</div>
            <div class="feedback-area">
              <el-form label-position="top">
                <el-form-item label="反馈类型">
                  <el-radio-group v-model="feedbackEvent">
                    <el-radio-button value="struggle">😣 卡住了</el-radio-button>
                    <el-radio-button value="mastered">✅ 已掌握</el-radio-button>
                    <el-radio-button value="skip">⏭️ 暂时跳过</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="补充说明（可选）">
                  <el-input v-model="feedbackDetail" type="textarea" :rows="3" placeholder="描述你的情况..." />
                </el-form-item>
                <el-button type="primary" @click="submitFeedback" :loading="learnStore.isLoading" style="width:100%">
                  提交反馈 → 优化路径
                </el-button>
              </el-form>
            </div>
          </div>

          <transition name="slide">
            <div v-if="learnStore.showAdjustment" class="card adjustment-card">
              <div class="card-title">🔔 优化 Agent 通知</div>
              <div class="adjustment-text" v-html="formattedAdjustment"></div>
              <div style="margin-top:12px;display:flex;gap:8px">
                <el-button type="primary" size="small" @click="learnStore.dismissAdjustment()">接受调整</el-button>
                <el-button size="small" @click="learnStore.dismissAdjustment()">关闭</el-button>
              </div>
            </div>
          </transition>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useLearnStore, usePathStore, useStudentStore } from '@/stores'
import type { PathItem } from '@/types'

const learnStore = useLearnStore()
const pathStore = usePathStore()
const studentStore = useStudentStore()

const currentIdx = ref(0)
const feedbackEvent = ref<'struggle' | 'mastered' | 'skip'>('struggle')
const feedbackDetail = ref('')

const currentItem = computed(() => learnStore.currentPath[currentIdx.value])

const oldPathTitles = ref<Set<string>>(new Set())

const formattedAdjustment = computed(() => learnStore.adjustmentReason.replace(/\n/g, '<br>'))

function isNewItem(item: PathItem) {
  return !oldPathTitles.value.has(item.title)
}

async function submitFeedback() {
  const sid = studentStore.studentId
  if (!sid) {
    ElMessage.error('请先完成画像录入')
    return
  }
  const item = currentItem.value
  if (!item) return

  oldPathTitles.value = new Set(learnStore.currentPath.map(p => p.title))

  try {
    await learnStore.submitInteraction(sid, feedbackEvent.value, item.concept_id, feedbackDetail.value || null)
    ElMessage.success('反馈已提交，路径已优化！')
    feedbackDetail.value = ''
  } catch {
    ElMessage.error('反馈提交失败，请重试')
  }
}

onMounted(() => {
  if (learnStore.currentPath.length === 0 && pathStore.isPathGenerated) {
    learnStore.setCurrentPath(pathStore.pathData)
  }
})
</script>

<style scoped>
.current-task {
  padding: 16px 24px;
}
.task-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  font-weight: 500;
}
.task-title {
  font-size: 18px;
  font-weight: 600;
  margin-top: 8px;
}
.task-reason {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.path-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.path-item-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.path-item-row:hover {
  border-color: #409eff;
  background: #ecf5ff;
}
.path-item-row.active {
  border-color: #409eff;
  background: #ecf5ff;
}
.path-item-row.highlight {
  border-color: #e6a23c;
  background: #fdf6ec;
  animation: highlight-pulse 1.5s ease-in-out;
}
@keyframes highlight-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(230,162,60,0); }
  50% { box-shadow: 0 0 0 4px rgba(230,162,60,0.2); }
}
.item-index {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}
.item-body {
  flex: 1;
}
.item-concept {
  font-size: 12px;
  color: #909399;
}
.item-title {
  font-size: 14px;
  font-weight: 500;
}
.feedback-area {
  padding: 4px 0;
}
.adjustment-card {
  border: 2px solid #e6a23c;
  background: #fdf6ec;
}
.adjustment-text {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}
</style>
