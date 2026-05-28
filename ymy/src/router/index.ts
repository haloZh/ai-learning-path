import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/profile' },
    { path: '/profile', name: 'profile', component: () => import('@/views/ProfileView.vue') },
    { path: '/diagnose', name: 'diagnose', component: () => import('@/views/DiagnoseView.vue') },
    { path: '/path', name: 'path', component: () => import('@/views/PathView.vue') },
    { path: '/learn', name: 'learn', component: () => import('@/views/LearnView.vue') },
    { path: '/assess', name: 'assess', component: () => import('@/views/AssessView.vue') }
  ]
})

export default router
