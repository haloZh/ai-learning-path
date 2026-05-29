<template>
  <div class="page-container">
    <!-- 反馈优化也走 LLM,需 loading 蒙版 -->
    <div v-if="learnStore.isLoading" class="learn-loading-mask">
      <div class="learn-loading-card">
        <el-icon :size="36" class="rotate" color="#409eff"><Loading /></el-icon>
        <div class="lm-title">优化 Agent 调整中…</div>
        <div class="lm-desc">LLM 在重新规划路径,约 5–30 秒</div>
      </div>
    </div>

    <h2 class="page-title">📖 学习工作台</h2>

    <div v-if="learnStore.currentPath.length === 0" class="card" style="text-align:center;padding:40px">
      <p style="color:#909399">暂无学习任务，请先完成诊断测验并生成路径</p>
      <el-button type="primary" @click="$router.push('/diagnose')" style="margin-top:12px">去诊断 →</el-button>
    </div>

    <template v-else>
      <!-- 全部完成庆祝卡片 -->
      <div v-if="progressPercent === 100" class="card celebrate-card">
        <div class="celebrate-emoji">🎉</div>
        <div class="celebrate-title">恭喜！全部学习项已完成</div>
        <div class="celebrate-stats">
          <div class="cs-item">
            <div class="cs-num">{{ learnStore.currentPath.length }}</div>
            <div class="cs-label">已完成项</div>
          </div>
          <div class="cs-item">
            <div class="cs-num">{{ totalLearnedMinutes }}</div>
            <div class="cs-label">累计学习(分钟)</div>
          </div>
          <div class="cs-item">
            <div class="cs-num">{{ studentStore.profile?.nickname || '同学' }}</div>
            <div class="cs-label">学习者</div>
          </div>
        </div>
        <div class="celebrate-actions">
          <el-button @click="$router.push('/assess')">📊 查看评估看板</el-button>
          <el-button type="primary" @click="$router.push('/diagnose')">🔁 再次诊断检验</el-button>
        </div>
      </div>

      <!-- 顶部进度条 -->
      <div class="card progress-card">
        <div class="progress-head">
          <span class="progress-title">学习进度</span>
          <span class="progress-count">{{ completedCount }} / {{ learnStore.currentPath.length }}</span>
        </div>
        <el-progress
          :percentage="progressPercent"
          :stroke-width="14"
          :status="progressPercent === 100 ? 'success' : ''"
        />
      </div>

      <!-- 当前学习卡片 -->
      <div class="card current-task" v-if="currentItem">
        <div class="task-header">
          <el-tag size="small" effect="dark">📍 学习中 · 第 {{ currentIdx + 1 }} 项</el-tag>
          <span class="task-concept">{{ currentItem.concept_id }}</span>
          <el-tag size="small">⏱ {{ currentItem.estimated_minutes }} 分钟</el-tag>
          <el-tag v-if="learnStore.isMock" type="warning" size="small">⚠️ Mock</el-tag>
          <el-tag v-if="isCurrentCompleted" type="success" size="small">✓ 已完成</el-tag>
        </div>
        <div class="task-title">{{ currentItem.title }}</div>
        <div v-if="currentItem.reason" class="task-reason">💡 {{ currentItem.reason }}</div>
        <div class="task-actions">
          <el-button
            :type="isCurrentCompleted ? 'default' : 'success'"
            @click="markComplete"
          >{{ isCurrentCompleted ? '↶ 取消完成' : '✓ 标记完成' }}</el-button>
          <el-tooltip content="该资源暂无外链,后续会补全" placement="top" :disabled="!!resourceUrl">
            <el-button :type="resourceUrl ? 'primary' : 'info'" :disabled="!resourceUrl" @click="openResource">
              {{ resourceUrl ? '🔗 打开学习资源' : '🔒 资源待补充' }}
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <el-row :gutter="20">
        <!-- 左:路径列表 -->
        <el-col :span="14">
          <div class="card">
            <div class="card-title">📚 学习路径项（点击切换当前学习）</div>
            <div class="path-list">
              <div
                v-for="(item, idx) in learnStore.currentPath" :key="idx"
                class="path-item-row"
                :class="{
                  active: idx === currentIdx,
                  completed: isItemCompleted(item),
                  highlight: isNewItem(item),
                }"
                @click="currentIdx = idx"
              >
                <span class="item-index">
                  <el-icon v-if="isItemCompleted(item)" color="#67c23a"><CircleCheckFilled /></el-icon>
                  <span v-else>{{ idx + 1 }}</span>
                </span>
                <div class="item-body">
                  <div class="item-concept">{{ item.concept_id }}</div>
                  <div class="item-title">{{ item.title }}</div>
                </div>
                <el-tag size="small" type="info">{{ item.estimated_minutes }}min</el-tag>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右:反馈 + 调整 -->
        <el-col :span="10">
          <div class="card">
            <div class="card-title">💬 学习反馈</div>
            <el-form label-position="top">
              <el-form-item label="反馈类型">
                <el-radio-group v-model="feedbackEvent" style="display:flex;flex-direction:column;gap:8px">
                  <el-radio value="struggle">😣 卡住了 — Agent 会插入补强练习</el-radio>
                  <el-radio value="mastered">✅ 已掌握 — Agent 会跳过该节点</el-radio>
                  <el-radio value="skip">⏭️ 暂时跳过 — 移到路径末尾复习</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="补充说明（可选）">
                <el-input v-model="feedbackDetail" type="textarea" :rows="3" placeholder="例如：判别式总是算错" maxlength="100" show-word-limit />
              </el-form-item>
              <el-button type="primary" @click="submitFeedback" :loading="learnStore.isLoading" style="width:100%">
                提交反馈 → 优化 Agent 调整路径
              </el-button>
            </el-form>
          </div>

          <transition name="slide">
            <div v-if="learnStore.showAdjustment" class="card adjustment-card">
              <div class="card-title">🔔 优化 Agent 通知</div>
              <div class="adjustment-stats">
                <span>新增项: <b style="color:#67c23a">{{ adjustmentDelta.added }}</b></span>
                <span>删除项: <b style="color:#f56c6c">{{ adjustmentDelta.removed }}</b></span>
              </div>
              <div class="adjustment-text" v-html="formattedAdjustment"></div>
              <div style="margin-top:12px;display:flex;gap:8px">
                <el-button type="success" size="small" @click="acceptAdjustment">✓ 接受调整</el-button>
                <el-button size="small" @click="rejectAdjustment">✗ 保留旧路径</el-button>
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
import { CircleCheckFilled, Loading } from '@element-plus/icons-vue'
import { useLearnStore, usePathStore, useStudentStore } from '@/stores'
import type { PathItem } from '@/types'

const learnStore = useLearnStore()
const pathStore = usePathStore()
const studentStore = useStudentStore()

const totalLearnedMinutes = computed(() =>
  learnStore.currentPath
    .filter(it => learnStore.isCompleted(`${it.concept_id}::${it.title}`))
    .reduce((s, it) => s + (it.estimated_minutes || 0), 0)
)

const currentIdx = ref(0)
const feedbackEvent = ref<'struggle' | 'mastered' | 'skip'>('struggle')
const feedbackDetail = ref('')

const currentItem = computed(() => learnStore.currentPath[currentIdx.value])

const itemKey = (it: PathItem) => `${it.concept_id}::${it.title}`

const oldPathKeys = ref<Set<string>>(new Set())
const formattedAdjustment = computed(() => learnStore.adjustmentReason.replace(/\n/g, '<br>'))

const completedCount = computed(() =>
  learnStore.currentPath.filter(it => learnStore.isCompleted(itemKey(it))).length
)
const progressPercent = computed(() => {
  const n = learnStore.currentPath.length
  return n ? Math.round((completedCount.value / n) * 100) : 0
})

const isCurrentCompleted = computed(() =>
  currentItem.value ? learnStore.isCompleted(itemKey(currentItem.value)) : false
)

// 资源 url:目前 PathItem 没带 url,占位
const resourceUrl = computed<string | null>(() => null)

const adjustmentDelta = computed(() => {
  let added = 0, removed = 0
  const newKeys = new Set(learnStore.newPath.map(itemKey))
  for (const it of learnStore.newPath) {
    if (!oldPathKeys.value.has(itemKey(it))) added++
  }
  for (const k of oldPathKeys.value) {
    if (!newKeys.has(k)) removed++
  }
  return { added, removed }
})

function isItemCompleted(it: PathItem) {
  return learnStore.isCompleted(itemKey(it))
}

function isNewItem(it: PathItem) {
  // 仅在调整通知期间高亮
  if (!learnStore.showAdjustment) return false
  return !oldPathKeys.value.has(itemKey(it))
}

function markComplete() {
  if (!currentItem.value) return
  learnStore.toggleCompleted(itemKey(currentItem.value))
}

function openResource() {
  if (resourceUrl.value) window.open(resourceUrl.value, '_blank')
}

async function submitFeedback() {
  const sid = studentStore.studentId
  if (!sid) {
    ElMessage.error('请先完成画像录入')
    return
  }
  const item = currentItem.value
  if (!item) return

  oldPathKeys.value = new Set(learnStore.currentPath.map(itemKey))

  try {
    await learnStore.submitInteraction(sid, feedbackEvent.value, item.concept_id, feedbackDetail.value || null)
    ElMessage.success('反馈已提交，请确认是否接受路径调整')
    feedbackDetail.value = ''
  } catch {
    ElMessage.error('反馈提交失败，请重试')
  }
}

function acceptAdjustment() {
  learnStore.acceptAdjustment()
  pathStore.setPath(learnStore.currentPath)
  ElMessage.success('已采用新路径')
}

function rejectAdjustment() {
  learnStore.rejectAdjustment()
  ElMessage.info('已保留旧路径，调整建议已忽略')
}

onMounted(() => {
  if (learnStore.currentPath.length === 0 && pathStore.isPathGenerated) {
    learnStore.setCurrentPath(pathStore.pathData)
  }
  // 从路径页跳过来时定位到点击的项
  if (learnStore.initialIdx >= 0 && learnStore.initialIdx < learnStore.currentPath.length) {
    currentIdx.value = learnStore.initialIdx
    learnStore.setInitialIdx(0) // 用完即重置
  }
})
</script>

<style scoped>
.celebrate-card {
  background: linear-gradient(135deg, #ecfccb 0%, #d4f1ce 100%);
  border: 1px solid #aed581;
  text-align: center;
  padding: 28px 24px;
  position: relative;
  overflow: hidden;
}
.celebrate-card::before {
  content: '🎊';
  position: absolute;
  top: 12px;
  left: 24px;
  font-size: 24px;
  opacity: 0.7;
}
.celebrate-card::after {
  content: '🌟';
  position: absolute;
  top: 12px;
  right: 24px;
  font-size: 24px;
  opacity: 0.7;
}
.celebrate-emoji {
  font-size: 48px;
  animation: bounce 1.5s ease-in-out infinite;
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
.celebrate-title {
  font-size: 22px;
  font-weight: 700;
  color: #2e7d32;
  margin-top: 8px;
  margin-bottom: 18px;
}
.celebrate-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 20px;
}
.cs-item {
  text-align: center;
}
.cs-num {
  font-size: 28px;
  font-weight: 700;
  color: #2e7d32;
  font-family: 'SF Mono', ui-monospace, monospace;
}
.cs-label {
  font-size: 12px;
  color: #606266;
  margin-top: 2px;
}
.celebrate-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}
.progress-card {
  padding: 16px 20px;
}
.progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.progress-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.progress-count {
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 14px;
  color: #409eff;
  font-weight: 600;
}
.current-task {
  background: linear-gradient(135deg, #ecf5ff 0%, #fff 100%);
  border-left: 4px solid #409eff;
  padding: 18px 24px;
}
.task-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}
.task-concept {
  font-size: 13px;
  color: #606266;
}
.task-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
}
.task-reason {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}
.task-actions {
  display: flex;
  gap: 12px;
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
  box-shadow: 0 0 0 2px rgba(64,158,255,0.15);
}
.path-item-row.completed {
  background: #f0f9eb;
  border-color: #c2e7b0;
}
.path-item-row.completed .item-title {
  color: #909399;
  text-decoration: line-through;
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
.path-item-row.completed .item-index {
  background: transparent;
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
.adjustment-card {
  border: 2px solid #e6a23c;
  background: #fdf6ec;
}
.adjustment-stats {
  display: flex;
  gap: 16px;
  padding: 8px 12px;
  background: rgba(255,255,255,0.5);
  border-radius: 6px;
  margin-bottom: 10px;
  font-size: 13px;
}
.adjustment-text {
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
  max-height: 200px;
  overflow-y: auto;
}
.rotate {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  100% { transform: rotate(360deg); }
}
.learn-loading-mask {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.learn-loading-card {
  background: #fff;
  padding: 24px 36px;
  border-radius: 12px;
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.12);
  text-align: center;
  min-width: 260px;
}
.lm-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-top: 12px;
}
.lm-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}
</style>
