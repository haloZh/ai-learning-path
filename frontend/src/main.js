import { createApp } from 'vue'
// hash 模式:URL 形如 /#/profile,服务端无需 SPA fallback,
// 也不会与 GET /profile 等后端 API 冲突。
import { createRouter, createWebHashHistory } from 'vue-router'

import App from './App.vue'
import ProfileView from './views/ProfileView.vue'
import DiagnoseView from './views/DiagnoseView.vue'
import PathView from './views/PathView.vue'
import StudyView from './views/StudyView.vue'

import 'katex/dist/katex.min.css'
import './assets/style.css'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/profile' },
    { path: '/profile', component: ProfileView, name: 'profile' },
    { path: '/diagnose', component: DiagnoseView, name: 'diagnose' },
    { path: '/path', component: PathView, name: 'path' },
    { path: '/study', component: StudyView, name: 'study' },
  ],
})

createApp(App).use(router).mount('#app')
