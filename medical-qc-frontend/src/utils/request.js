// src/utils/request.js
import axios from 'axios'

let router = null

export const setRouter = (r) => {
  router = r
}

const instance = axios.create({
  // 默认为空字符串，使用相对路径 /api/v1，这样请求会经过 Vite 的代理
  baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1',
  timeout: 30000, // 增加超时时间，AI分析可能较慢
})

// 请求拦截器：自动添加 Token
instance.interceptors.request.use((config) => {
  // ✅ 统一使用 'access_token' (sessionStorage)
  const token = sessionStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理登录过期
instance.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // ✅ 删除正确的 key
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('user_info') // 同时清除用户信息

      if (router) {
        router.push('/login')
      } else {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export default instance
