<template>
  <el-container class="app-layout">
    <el-aside :width="isCollapsed ? '64px' : '200px'" class="app-sidebar">
      <div class="sidebar-logo" @click="isCollapsed = !isCollapsed">
        <span v-if="!isCollapsed" class="logo-text">AI学习路径</span>
        <span v-else class="logo-icon">🤖</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapsed"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title>画像录入</template>
        </el-menu-item>
        <el-menu-item index="/diagnose">
          <el-icon><Search /></el-icon>
          <template #title>诊断测验</template>
        </el-menu-item>
        <el-menu-item index="/path">
          <el-icon><MapLocation /></el-icon>
          <template #title>路径视图</template>
        </el-menu-item>
        <el-menu-item index="/learn">
          <el-icon><Reading /></el-icon>
          <template #title>学习工作台</template>
        </el-menu-item>
        <el-menu-item index="/assess">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>评估看板</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <span class="header-title">AI赋能下的个性化学习路径系统</span>
          <el-tag type="info" size="small">演示版</el-tag>
        </div>
        <div class="header-right">
          <el-tag v-if="studentStore.profile" type="success" effect="plain">
            👤 {{ studentStore.profile.nickname }}
          </el-tag>
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
import { useRoute } from 'vue-router'
import { User, Search, MapLocation, Reading, DataAnalysis } from '@element-plus/icons-vue'
import { useStudentStore } from '@/stores'

const route = useRoute()
const studentStore = useStudentStore()
const isCollapsed = ref(false)
const currentRoute = computed(() => route.path)
</script>

<style scoped>
.app-layout {
  height: 100vh;
}
.app-sidebar {
  background: #1a1a2e;
  transition: width 0.3s;
  overflow: hidden;
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
.sidebar-menu .el-menu-item.is-active {
  background: rgba(64,158,255,0.15) !important;
  border-right: 3px solid #409eff;
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
.app-main {
  background: #f0f2f5;
  overflow-y: auto;
}
</style>
