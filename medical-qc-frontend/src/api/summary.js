import request from '@/utils/request'

// 获取异常汇总统计数据
export const getSummaryStats = () => {
  return request({
    url: '/summary/stats',
    method: 'get'
  })
}

// 获取异常趋势数据
export const getIssueTrend = (days = 7) => {
  return request({
    url: '/summary/trend',
    method: 'get',
    params: { days }
  })
}

// 获取异常类型分布数据
export const getIssueDistribution = () => {
  return request({
    url: '/summary/distribution',
    method: 'get'
  })
}

// 获取最近异常记录列表
export const getRecentIssues = (params) => {
  return request({
    url: '/summary/recent',
    method: 'get',
    params
  })
}
