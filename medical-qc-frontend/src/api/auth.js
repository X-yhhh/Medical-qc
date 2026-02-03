// src/api/auth.js
// ----------------------------------------------------------------------------------
// 认证模块前端 API (Auth API)
// 作用：提供前端登录、注册的接口调用方法。
// 对接后端：/api/v1/auth
// ----------------------------------------------------------------------------------

import request from '@/utils/request'

// 用户登录
// 参数：{ username, password }
export const login = (data) => {
  return request.post('/auth/login', data)
}

// 用户注册
// 参数：{ username, password, email, full_name, ... }
export const register = (data) => {
  return request.post('/auth/register', data)
}
