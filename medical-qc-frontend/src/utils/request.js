// src/utils/request.js
/**
 * @file src/utils/request.js
 * @description Axios 请求封装模块
 * 主要功能：
 * 1. 创建全局唯一的 Axios 实例，配置 BaseURL 和超时时间。
 * 2. 请求拦截器：自动在 Header 中添加 JWT Token。
 * 3. 响应拦截器：统一处理 API 响应错误，特别是 401 未授权自动登出。
 */

import axios from 'axios'

let router = null

// 注入路由实例 (避免循环引用)
export const setRouter = (r) => {
  router = r
}

// 创建 Axios 实例
const instance = axios.create({
  // BaseURL 配置：优先使用环境变量，否则默认为相对路径 /api/v1 (走 Vite 代理)
  baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1',
  timeout: 30000, // 超时时间：30秒 (AI 分析可能较慢)
})

// ----------------------------------------------------------------------------------
// 请求拦截器 (Request Interceptor)
// 作用：在发送请求前统一处理配置
// ----------------------------------------------------------------------------------
instance.interceptors.request.use((config) => {
  // 从 sessionStorage 获取 Token
  const token = sessionStorage.getItem('access_token')
  
  // 如果 Token 存在，添加到 Authorization 头
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ----------------------------------------------------------------------------------
// 响应拦截器 (Response Interceptor)
// 作用：在接收响应后统一处理结果或错误
// ----------------------------------------------------------------------------------
instance.interceptors.response.use(
  // 成功：直接返回 data 部分，简化调用方代码
  (response) => response.data,
  
  // 失败：统一错误处理
  (error) => {
    // 处理 401 Unauthorized (Token 过期或无效)
    if (error.response?.status === 401) {
      // 1. 清除本地存储的凭证
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('user_info')

      // 2. 跳转回登录页
      if (router) {
        router.push('/login')
      } else {
        window.location.href = '/login'
      }
    }
    // 继续抛出错误，供调用方具体处理
    return Promise.reject(error)
  },
)

export default instance
