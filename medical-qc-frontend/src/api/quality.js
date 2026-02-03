// src/api/quality.js
// 所有质控检测的模拟 API（未来替换为真实 axios 调用）
import request from '@/utils/request'

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

// 改名为 predictHemorrhage 以匹配 Vue 组件中的导入
export const predictHemorrhage = async (file, metadata = {}) => {
  const formData = new FormData()
  formData.append('file', file)
  if (metadata.patientName) formData.append('patient_name', metadata.patientName)
  if (metadata.examId) formData.append('exam_id', metadata.examId)

  try {
    // 使用新的持久化接口
    const response = await request.post('/quality/hemorrhage/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response // request.js 已经返回 response.data
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

export const getHemorrhageHistory = async (limit = 20) => {
  try {
    const response = await request.get('/quality/hemorrhage/history', {
      params: { limit }
    })
    return response
  } catch (error) {
    console.error('获取历史记录失败:', error)
    return []
  }
}
