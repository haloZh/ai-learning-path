<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <div class="page">
        <header class="header">
          <div class="title-row">
            <span class="logo">🎯</span>
            <h1>个性化学习路径系统</h1>
          </div>
          <div class="sub">L-2 项目 · 北科大 MBA · 人工智能课大作业</div>
        </header>

        <div class="stepbar">
          <router-link
            v-for="(s, i) in steps"
            :key="s.path"
            :to="s.path"
            :class="['step', { active: $route.name === s.name, disabled: isDisabled(i) }]"
          >
            <span class="step-num">{{ i + 1 }}</span>
            <span class="step-label">{{ s.icon }} {{ s.label }}</span>
          </router-link>
        </div>

        <main class="main">
          <router-view />
        </main>

        <footer class="footer">
          <span>FastAPI + LangGraph + 火山方舟 Doubao + bge-m3 / Chroma · SQLite</span>
          <span>·</span>
          <a href="/docs" target="_blank">API 文档</a>
        </footer>
      </div>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { themeOverrides } from './theme'
import { store } from './store'

const route = useRoute()

const steps = [
  { path: '/profile', name: 'profile', label: '学生画像', icon: '📋' },
  { path: '/diagnose', name: 'diagnose', label: '模拟答卷', icon: '✏️' },
  { path: '/path', name: 'path', label: '诊断结果', icon: '🎯' },
  { path: '/study', name: 'study', label: '学习交互', icon: '🔄' },
]

function isDisabled(i) {
  if (i === 0) return false
  if (i === 1) return !store.studentId
  return !store.diagnoseResult
}
</script>
