// src/api/quality.js
// ----------------------------------------------------------------------------------
// 质控模块前端 API (Quality API)
// 作用：提供各类影像质控检测的接口调用。
// 说明：目前除脑出血检测外，其他质控项使用 Mock (模拟) 数据。
// 对接后端：/api/v1/quality
// ----------------------------------------------------------------------------------

import request from '@/utils/request'

// ======================
// 模拟接口 (Mock APIs)
// 作用：前端演示用，暂未对接真实后端算法
// ======================

// 模拟：头部平扫质控
export const detectHead = (file) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        issues: [
          { item: '运动伪影', status: Math.random() > 0.7 ? '不合格' : '合格' },
          { item: '金属伪影', status: Math.random() > 0.8 ? '不合格' : '合格' },
          { item: 'FOV过大', status: Math.random() > 0.6 ? '不合格' : '合格' },
          { item: 'FOV过小', status: Math.random() > 0.5 ? '不合格' : '合格' },
          { item: '层厚不当', status: Math.random() > 0.4 ? '不合格' : '合格' }
        ],
        duration: Math.floor(800 + Math.random() * 500)
      })
    }, 1200)
  })
}

// 模拟：胸部平扫质控
export const detectChestNonContrast = (file) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        issues: [
          { item: '呼吸伪影', status: Math.random() > 0.6 ? '不合格' : '合格' },
          { item: '体外金属', status: Math.random() > 0.8 ? '不合格' : '合格' },
          { item: '扫描范围不全', status: Math.random() > 0.5 ? '不合格' : '合格' }
        ],
        duration: Math.floor(900 + Math.random() * 400)
      })
    }, 1300)
  })
}

// 模拟：胸部增强质控
export const detectChestContrast = (file) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        issues: [
          { item: '分期错误', status: Math.random() > 0.7 ? '不合格' : '合格' },
          { item: '增强时机不当', status: Math.random() > 0.6 ? '不合格' : '合格' },
          { item: 'FOV过小', status: Math.random() > 0.4 ? '不合格' : '合格' }
        ],
        duration: Math.floor(1000 + Math.random() * 600)
      })
    }, 1400)
  })
}

// 模拟：冠脉CTA质控
export const detectCoronaryCTA = (file) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        issues: [
          { item: '血管强化不足', status: Math.random() > 0.5 ? '不合格' : '合格' },
          { item: '噪声过大', status: Math.random() > 0.6 ? '不合格' : '合格' },
          { item: '心电门控失败', status: Math.random() > 0.7 ? '不合格' : '合格' }
        ],
        duration: Math.floor(1200 + Math.random() * 800)
      })
    }, 1600)
  })
}

// ======================
// 真实接口 (Real APIs)
// 作用：对接后端 AI 服务
// ======================

// 脑出血智能检测
// 对接后端：POST /api/v1/quality/hemorrhage
export const predictHemorrhage = async (file, metadata = {}) => {
  const formData = new FormData()
  formData.append('file', file)
  if (metadata.patientName) formData.append('patient_name', metadata.patientName)
  if (metadata.examId) formData.append('exam_id', metadata.examId)

  try {
    // 修正：后端接口路径为 /quality/hemorrhage
    const response = await request.post('/quality/hemorrhage', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response // request.js 响应拦截器已处理 data
  } catch (error) {
    console.error('脑出血检测失败:', error)

    if (error.response) {
      throw new Error(`后端返回错误: ${error.response.status} ${error.response.statusText}`)
    } else if (error.request) {
      throw new Error('网络错误：无法连接到后端服务')
    } else {
      throw new Error(`请求配置错误: ${error.message}`)
    }
  }
}

// 获取历史检测记录
// 对接后端：待实现
export const getHemorrhageHistory = async (limit = 20) => {
  try {
    // TODO: 后端暂未实现此接口，预留位置
    // const response = await request.get('/quality/hemorrhage/history', { params: { limit } })
    return { data: [] } // 临时返回空数据
  } catch (error) {
    console.error('获取历史记录失败', error)
    return { data: [] }
  }
}
