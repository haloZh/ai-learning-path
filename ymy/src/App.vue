<template>
  <el-container class="app-layout">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="app-sidebar">
      <div class="sidebar-logo" @click="isCollapsed = !isCollapsed">
        <span v-if="!isCollapsed" class="logo-text">AI 学习路径</span>
        <span v-else class="logo-icon">🤖</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapsed"
        router
        class="sidebar-menu"
      >
        <el-menu-item
          v-for="step in steps"
          :key="step.path"
          :index="step.path"
          :disabled="step.disabled"
          @click.capture="onMenuClick(step, $event)"
        >
          <el-icon><component :is="step.icon" /></el-icon>
          <template #title>
            <span style="display:flex;align-items:center;gap:6px;justify-content:space-between;width:100%">
              <span>{{ step.label }}</span>
              <el-icon v-if="step.disabled" style="opacity:.5"><Lock /></el-icon>
              <el-icon v-else-if="step.done" style="color:#67c23a"><CircleCheck /></el-icon>
            </span>
          </template>
        </el-menu-item>
      </el-menu>
      <div v-if="!isCollapsed" class="sidebar-footer">
        <div class="footer-line">L-2 项目</div>
        <div class="footer-line">北科大 MBA · AI 大作业</div>
        <div class="footer-tech">FastAPI · LangGraph · bge-m3</div>
      </div>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <span class="header-title">AI 赋能下的个性化学习路径系统</span>
        </div>
        <div class="header-right">
          <span class="progress-hint">{{ progressHint }}</span>
          <el-tag v-if="studentStore.profile" type="success" effect="plain" round>
            👤 {{ studentStore.profile.nickname }}
          </el-tag>
          <el-button v-if="studentStore.profile" size="small" text @click="onReset">重置</el-button>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Search, MapLocation, Reading, DataAnalysis,
  Lock, CircleCheck,
} from '@element-plus/icons-vue'
import { useStudentStore, useDiagnoseStore, usePathStore, clearPersisted } from '@/stores'

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()
const diagnoseStore = useDiagnoseStore()
const pathStore = usePathStore()
const isCollapsed = ref(false)

const currentRoute = computed(() => route.path)

const steps = computed(() => [
  {
    path: '/profile',
    label: '画像录入',
    icon: User,
    disabled: false,
    done: !!studentStore.profile,
  },
  {
    path: '/diagnose',
    label: '诊断测验',
    icon: Search,
    disabled: !studentStore.profile,
    done: diagnoseStore.isDiagnosed,
  },
  {
    path: '/path',
    label: '路径视图',
    icon: MapLocation,
    disabled: !diagnoseStore.isDiagnosed,
    done: pathStore.isPathGenerated,
  },
  {
    path: '/learn',
    label: '学习工作台',
    icon: Reading,
    disabled: !pathStore.isPathGenerated,
    done: false,
  },
  {
    path: '/assess',
    label: '评估看板',
    icon: DataAnalysis,
    disabled: !diagnoseStore.isDiagnosed,
    done: false,
  },
])

const progressHint = computed(() => {
  if (!studentStore.profile) return '请先完成第 1 步：画像录入'
  if (!diagnoseStore.isDiagnosed) return '请完成第 2 步：诊断测验'
  if (!pathStore.isPathGenerated) return '请查看第 3 步：学习路径'
  return '✓ 全流程已开通'
})

function onMenuClick(step: any, e: Event) {
  if (step.disabled) {
    e.preventDefault()
    e.stopPropagation()
    ElMessage.warning(`请先完成前置步骤后再访问"${step.label}"`)
  }
}

async function onReset() {
  try {
    await ElMessageBox.confirm(
      '将清除当前学生画像、诊断结果与路径,本会话内将无法恢复。继续吗?',
      '重置会话',
      { type: 'warning', confirmButtonText: '确认重置', cancelButtonText: '取消' },
    )
  } catch { return }
  clearPersisted()
  // 强制刷新让 Pinia 重新初始化
  router.push('/profile')
  setTimeout(() => location.reload(), 100)
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
}
.app-sidebar {
  background: #1a1a2e;
  transition: width 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.sidebar-menu {
  flex: 1;
}
.sidebar-footer {
  padding: 14px 18px;
  border-top: 1px solid rgba(255,255,255,0.08);
  text-align: center;
  font-size: 11px;
  line-height: 1.6;
}
.footer-line {
  color: rgba(255,255,255,0.6);
}
.footer-tech {
  color: rgba(255,255,255,0.35);
  font-family: 'SF Mono', ui-monospace, monospace;
  font-size: 10px;
  margin-top: 4px;
}
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
}
.logo-icon {
  font-size: 24px;
}
.sidebar-menu {
  border-right: none;
  background: transparent;
  --el-menu-bg-color: transparent;
  --el-menu-text-color: rgba(255,255,255,0.7);
  --el-menu-active-color: #409eff;
  --el-menu-hover-bg-color: rgba(255,255,255,0.05);
}
.sidebar-menu :deep(.el-menu-item.is-active) {
  background: rgba(64,158,255,0.15) !important;
  border-right: 3px solid #409eff;
}
.sidebar-menu :deep(.el-menu-item.is-disabled) {
  color: rgba(255,255,255,0.3) !important;
  cursor: not-allowed;
}
.app-header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  padding: 0 24px;
  height: 60px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.progress-hint {
  font-size: 13px;
  color: #909399;
}
.app-main {
  background: #f0f2f5;
  overflow-y: auto;
}
</style>
