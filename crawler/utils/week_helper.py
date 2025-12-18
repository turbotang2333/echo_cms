# -*- coding: utf-8 -*-
"""
自然周计算工具
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional


def _parse_date(date_str: str) -> Optional[datetime]:
    """
    支持格式:
    - YYYY/MM/DD
    - YYYY-MM-DD
    - MM/DD 或 MM-DD (默认当前年；若日期晚于今天 180 天，回退一年以避免跨年误判)
    """
    if not date_str:
        return None
    raw = date_str.strip()
    fmts = ["%Y/%m/%d", "%Y-%m-%d", "%m/%d", "%m-%d"]

    for fmt in fmts:
        try:
            dt = datetime.strptime(raw, fmt)
            # 无年份时补当前年
            if "%Y" not in fmt:
                dt = dt.replace(year=datetime.now().year)
                # 若日期比今天晚 180 天，认为跨年，回退一年
                if dt.date() > (datetime.now().date() + timedelta(days=180)):
                    dt = dt.replace(year=dt.year - 1)
            return dt
        except Exception:  # noqa: BLE001
            continue
    return None


def is_current_week(date_str: str) -> bool:
    """判断日期是否在本周（周一到周日）"""
    dt = _parse_date(date_str)
    if not dt:
        return False
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date() <= dt.date() <= sunday.date()


def get_week_range() -> tuple:
    """获取本周的起止日期"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.date(), sunday.date()

