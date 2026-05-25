<template>
  <header class="header">
    <h1>L-2 个性化学习路径系统</h1>
    <div class="sub">北科大 MBA · 人工智能课大作业 · AI 赋能下的个性化学习路径设计与实现</div>
  </header>
  <nav class="nav">
    <router-link to="/profile" class="tab">① 学生画像</router-link>
    <router-link to="/diagnose" class="tab" :class="{ disabled: !store.studentId }">② 模拟答卷</router-link>
    <router-link to="/path" class="tab" :class="{ disabled: !store.diagnoseResult }">③ 诊断结果</router-link>
    <router-link to="/study" class="tab" :class="{ disabled: !store.diagnoseResult }">④ 学习交互</router-link>
  </nav>
  <main class="main">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </main>
  <footer class="footer">
    后端 FastAPI + LangGraph + Doubao + bge-m3/Chroma · 数据库 SQLite ·
    <a href="/docs" target="_blank">API 文档(Swagger)</a>
  </footer>
</template>

<script setup>
import { store } from './store'
</script>
