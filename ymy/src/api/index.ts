import axios from 'axios'
import { ElMessage } from 'element-plus'

// 慢端点(诊断/交互)需走 LLM 多次,单次最多 ~3 分钟
const SLOW_ENDPOINTS = ['/diagnose', '/interaction']

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const url = config.url || ''
  if (SLOW_ENDPOINTS.some((p) => url.startsWith(p))) {
    config.timeout = 180000 // 3 分钟
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    let detail: string
    if (error.code === 'ECONNABORTED' || /timeout/i.test(error.message || '')) {
      detail = 'LLM 响应超时，请稍后重试或减少题量'
    } else {
      detail = error.response?.data?.detail || error.message || '请求失败'
    }
    ElMessage.error(detail)
    return Promise.reject(error)
  }
)

export default api
