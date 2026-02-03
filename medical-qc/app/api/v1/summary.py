# app/api/v1/summary.py
# ----------------------------------------------------------------------------------
# 异常汇总模块 API (Summary API)
# 作用：提供“异常汇总”页面的数据支持，包括统计看板、趋势图、分布图和异常列表。
# 注意：目前部分接口使用模拟数据 (Mock)，后续将连接数据库进行真实统计。
# 对接前端：
#   - views/summary/index.vue (整个异常汇总页面)
#   - components/summary/StatCard.vue (统计卡片)
#   - components/summary/TrendChart.vue (趋势图)
#   - components/summary/DistributionChart.vue (分布图)
#   - components/summary/IssueList.vue (异常列表)
# ----------------------------------------------------------------------------------

from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta

from app.api import deps
from app.models.user import User

router = APIRouter()

# ----------------------------------------------------------------------------------
# 接口：获取汇总统计数据
# URL: GET /api/v1/summary/stats
# 作用：返回看板顶部的关键指标（总异常数、今日异常、待处理等）。
# 对接前端：views/summary/index.vue 中的 fetchStats 方法
# ----------------------------------------------------------------------------------
@router.get("/stats", response_model=Dict[str, Any])
def get_summary_stats(
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取异常汇总统计数据
    
    作用：
        查询并计算全院影像质控的关键指标。
    
    返回字段：
        totalIssues: 累计异常总数
        todayIssues: 今日新增异常
        pendingIssues: 待处理异常
        resolutionRate: 解决率 (%)
        avgResolutionTime: 平均处理时间 (小时)
    """
    # TODO: 替换为真实数据库查询 (Count queries)
    # 模拟数据
    return {
        "totalIssues": 1284,       # 累计异常总数
        "todayIssues": 12,         # 今日新增异常
        "pendingIssues": 45,       # 待处理异常
        "resolutionRate": 96.5,    # 解决率
        "avgResolutionTime": 4.2   # 平均处理时间(小时)
    }

# ----------------------------------------------------------------------------------
# 接口：获取异常趋势数据
# URL: GET /api/v1/summary/trend
# 作用：返回指定天数内的异常数量趋势，用于 ECharts 折线图。
# 参数：days (默认7天)
# 对接前端：views/summary/index.vue 中的 fetchTrend 方法 (对应 ECharts 组件)
# ----------------------------------------------------------------------------------
@router.get("/trend", response_model=Dict[str, Any])
def get_issue_trend(
    days: int = Query(7, ge=1, le=365),
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取异常趋势数据
    
    作用：
        统计过去 N 天每天的异常检出数量和已解决数量。
    
    参数：
        days: 统计天数范围 (1-365)
    """
    dates = []
    counts = []
    solved = []
    
    # 生成过去 N 天的模拟趋势数据
    for i in range(days - 1, -1, -1):
        d = datetime.now() - timedelta(days=i)
        dates.append(f"{d.month}/{d.day}")
        counts.append(random.randint(5, 25))  # 每日异常数
        solved.append(random.randint(5, 20))  # 每日解决数
        
    return {
        "dates": dates,
        "counts": counts,
        "solved": solved
    }

# ----------------------------------------------------------------------------------
# 接口：获取异常分布数据
# URL: GET /api/v1/summary/distribution
# 作用：返回各类异常类型的占比，用于 ECharts 饼图。
# 对接前端：views/summary/index.vue 中的 fetchDistribution 方法
# ----------------------------------------------------------------------------------
@router.get("/distribution", response_model=List[Dict[str, Any]])
def get_issue_distribution(
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取异常类型分布数据
    
    作用：
        统计各类质控问题（如伪影、扫描范围不足等）的分布情况。
    """
    # 模拟常见质控问题分布
    return [
        { "value": 335, "name": '伪影问题' },
        { "value": 310, "name": '扫描范围不足' },
        { "value": 234, "name": '参数设置错误' },
        { "value": 135, "name": '增强效果不佳' },
        { "value": 1548, "name": '其他' }
    ]

# ----------------------------------------------------------------------------------
# 接口：获取最近异常列表
# URL: GET /api/v1/summary/recent
# 作用：返回分页的异常记录列表，支持搜索和状态过滤。
# 参数：page (页码), limit (每页数量), query (搜索关键词), status (状态)
# 对接前端：views/summary/index.vue 中的 fetchRecentIssues 方法 (表格组件)
# ----------------------------------------------------------------------------------
@router.get("/recent", response_model=Dict[str, Any])
def get_recent_issues(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    query: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取最近异常记录列表
    
    作用：
        获取最新的质控异常记录，用于列表展示。
        支持分页、关键词搜索和状态筛选。
    """
    # 模拟列表数据
    list_data = []
    statuses = ['待处理', '处理中', '已解决', '忽略']
    types = ['头部平扫', '胸部平扫', '胸部增强', '冠脉CTA', '脑出血检测']
    issues = ['运动伪影', '金属伪影', 'FOV过小', '造影剂外渗', '中线偏移', '脑室受压']
    names = ['张伟', '李娜', '王强', '刘洋', '陈敏', '赵刚', '孙丽', '周杰', '吴艳', '郑华']
    
    # 生成模拟数据
    for i in range(limit):
        # 如果有状态筛选，则强制使用该状态，否则随机
        current_status = status if status else statuses[random.randint(0, len(statuses)-1)]
        
        item = {
            "id": f"ISS-{int(datetime.now().timestamp())}-{i}",
            "date": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            "patientName": names[random.randint(0, len(names)-1)],
            "examId": f"ACC{random.randint(10000, 99999)}",
            "type": types[random.randint(0, len(types)-1)],
            "description": issues[random.randint(0, len(issues)-1)],
            "status": current_status,
            "priority": 'High' if random.random() > 0.7 else 'Normal',
            "imageUrl": f"https://placehold.co/600x400/eef/333?text=Medical+Image+{i}"
        }
        list_data.append(item)

    # 模拟总数
    return {
        "total": 100,
        "items": list_data
    }
