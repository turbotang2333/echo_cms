# -*- coding: utf-8 -*-
"""
自然周计算工具
"""
from datetime import datetime, timedelta

def is_current_week(date_str: str) -> bool:
    """判断日期是否在本周（周一到周日）"""
    # TODO: 实现自然周判断逻辑
    pass

def get_week_range() -> tuple:
    """获取本周的起止日期"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date(), sunday.date()







