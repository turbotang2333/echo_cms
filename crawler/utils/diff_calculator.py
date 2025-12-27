# -*- coding: utf-8 -*-
"""
数据差异计算工具
负责 day/week/month 差异计算与格式化
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def _parse_number(value: Any) -> Optional[float]:
    """
    将带中文单位/英文字母单位的数字字符串转换为 float
    支持: "6.8万" "3.2亿" "1,200" "5k" 纯数字/float/int
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return None

    raw = value.strip().lower().replace(",", "")
    if not raw or raw == "-" or raw == "null":
        return None

    multiplier = 1.0
    if "亿" in raw:
        raw = raw.replace("亿", "")
        multiplier = 1e8
    elif "万" in raw:
        raw = raw.replace("万", "")
        multiplier = 1e4
    elif raw.endswith("k"):
        raw = raw[:-1]
        multiplier = 1e3
    elif raw.endswith("w"):
        raw = raw[:-1]
        multiplier = 1e4

    num_str = ""
    for ch in raw:
        if ch.isdigit() or ch in ".-+":
            num_str += ch
        else:
            # 遇到非数字后直接停止，避免干扰
            break

    try:
        return float(num_str) * multiplier
    except Exception:  # noqa: BLE001
        return None


def _format_diff(delta: Optional[float]) -> str:
    if delta is None:
        return "0"
    if abs(delta) < 1e-9:
        return "0"

    sign = "+" if delta > 0 else "-"
    val = abs(delta)

    if val >= 1000:
        # 千级以上用 k，保留 1 位小数（去掉多余 0）
        v = round(val / 1000, 1)
        return f"{sign}{v:g}k"

    if val >= 10:
        # 10 以上取整数
        return f"{sign}{round(val):g}"

    # 小于 10 保留 1 位小数
    v = round(val, 1)
    return f"{sign}{v:.1f}".rstrip("0").rstrip(".")


def _build_value_map(dates: List[str], values: List[Any]) -> Dict[str, float]:
    """
    将日期与值构造成 date->float map，便于按天回溯
    """
    result: Dict[str, float] = {}
    size = min(len(dates), len(values))
    for idx in range(size):
        num = _parse_number(values[idx])
        if num is None:
            continue
        result[dates[idx]] = num
    return result


def _get_history_value(history_map: Dict[str, float], days_ago: int, today: datetime) -> Optional[float]:
    target_date = today - timedelta(days=days_ago)
    key = target_date.strftime("%m-%d")
    return history_map.get(key)


def calculate_diffs(current_basic: Dict[str, Any], trend_history: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    计算 day/week/month 差异
    - 依赖 trend_history 中的 dates + reservations/rating
    - followers/review_count 若无历史则返回 0
    """
    today = datetime.now()
    dates = trend_history.get("dates") or []
    history_maps = {
        "reservations": _build_value_map(dates, trend_history.get("reservations") or []),
        "rating": _build_value_map(dates, trend_history.get("rating") or []),
    }

    metrics = ["reservations", "rating", "followers", "review_count"]
    diffs: Dict[str, Dict[str, str]] = {}

    for metric in metrics:
        current_val = _parse_number(current_basic.get(metric))
        if current_val is None:
            diffs[metric] = {"day": "0", "week": "0", "month": "0"}
            continue

        hist_map = history_maps.get(metric, {})
        day_val = _get_history_value(hist_map, 1, today)
        week_val = _get_history_value(hist_map, 7, today)
        month_val = _get_history_value(hist_map, 30, today)

        diffs[metric] = {
            "day": _format_diff(current_val - day_val) if day_val is not None else "0",
            "week": _format_diff(current_val - week_val) if week_val is not None else "0",
            "month": _format_diff(current_val - month_val) if month_val is not None else "0",
        }

    return diffs










