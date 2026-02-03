from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta

from app.api import deps
from app.models.user import User

router = APIRouter()

@router.get("/stats", response_model=Dict[str, Any])
def get_summary_stats(
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取异常汇总统计数据
    """
    # 模拟数据 (后期替换为真实数据库查询)
    return {
        "totalIssues": 1284,
        "todayIssues": 12,
        "pendingIssues": 45,
        "resolutionRate": 96.5,
        "avgResolutionTime": 4.2
    }

@router.get("/trend", response_model=Dict[str, Any])
def get_issue_trend(
    days: int = Query(7, ge=1, le=365),
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取异常趋势数据
    """
    dates = []
    counts = []
    solved = []
    
    for i in range(days - 1, -1, -1):
        d = datetime.now() - timedelta(days=i)
        dates.append(f"{d.month}/{d.day}")
        counts.append(random.randint(5, 25))
        solved.append(random.randint(5, 20))
        
    return {
        "dates": dates,
        "counts": counts,
        "solved": solved
    }

@router.get("/distribution", response_model=List[Dict[str, Any]])
def get_issue_distribution(
    current_user: User = Depends(deps.get_current_user)
):
    """
    获取异常类型分布数据
    """
    return [
        { "value": 335, "name": '伪影问题' },
        { "value": 310, "name": '扫描范围不足' },
        { "value": 234, "name": '参数设置错误' },
        { "value": 135, "name": '增强效果不佳' },
        { "value": 1548, "name": '其他' }
    ]

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
    """
    # 模拟数据
    list_data = []
    statuses = ['待处理', '处理中', '已解决', '忽略']
    types = ['头部平扫', '胸部平扫', '胸部增强', '冠脉CTA', '脑出血检测']
    issues = ['运动伪影', '金属伪影', 'FOV过小', '造影剂外渗', '中线偏移', '脑室受压']
    names = ['张伟', '李娜', '王强', '刘洋', '陈敏', '赵刚', '孙丽', '周杰', '吴艳', '郑华']
    
    # 如果有状态筛选，优先生成该状态的数据
    
    for i in range(limit):
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
        
        # 简单的搜索过滤模拟
        if query:
            if query not in item["patientName"] and query not in item["examId"]:
                continue
                
        list_data.append(item)
        
    return {
        "total": 100, # 假装有100条
        "list": list_data
    }
