# -*- coding: utf-8 -*-
"""
竞品监控爬虫主入口
阶段二任务 2.1：主流程框架
"""
from __future__ import annotations

import json
import logging
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fetchers.bilibili import fetch_bilibili_data
from fetchers.taptap import fetch_taptap_data
from fetchers.weibo import fetch_weibo_data
from fetchers.xiaohongshu import fetch_xiaohongshu_data
from utils.diff_calculator import calculate_diffs
from utils.week_helper import is_current_week

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "public" / "games_config.json"
DATA_PATH = BASE_DIR / "public" / "data.json"
PLATFORMS = ["taptap", "bilibili", "weibo", "xiaohongshu"]

PLATFORM_FETCHERS = {
    "taptap": fetch_taptap_data,
    "bilibili": fetch_bilibili_data,
    "weibo": fetch_weibo_data,
    "xiaohongshu": fetch_xiaohongshu_data,
}


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("文件不存在，使用默认值: %s", path)
    except json.JSONDecodeError as exc:
        logging.error("JSON 解析失败 %s: %s", path, exc)
    return default


def safe_write_json(path: Path, data: Any) -> None:
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def init_game_record(game_cfg: Dict[str, Any], old_record: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    old_record = old_record or {}
    name = game_cfg.get("name") or old_record.get("name") or ""
    icon_char = (game_cfg.get("icon_url") or "") and "" or (name[:1] or old_record.get("icon_char") or "")

    record = {
        "id": game_cfg.get("id"),
        "name": name,
        "icon_char": old_record.get("icon_char", icon_char),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fetch_status": {platform: "not_configured" for platform in PLATFORMS},
        "basic_info": old_record.get("basic_info", {
            "status": "",
            "rating": None,
            "reservations": None,
            "followers": None,
            "review_count": None,
            "tags": [],
            "diffs": {},
        }),
        "trend_history": old_record.get("trend_history", {
            "dates": [],
            "reservations": [],
            "rating": [],
        }),
        "official_posts": _ensure_official_posts(old_record.get("official_posts")),
        "hot_reviews": old_record.get("hot_reviews", []),
    }
    return record


def _ensure_official_posts(raw_posts: Optional[Dict[str, List[Dict[str, Any]]]]) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {platform: [] for platform in PLATFORMS}
    if isinstance(raw_posts, dict):
        for platform, posts in raw_posts.items():
            if platform in result and isinstance(posts, list):
                result[platform] = posts
    return result


def merge_fetch_result(record: Dict[str, Any], platform: str, fetch_result: Dict[str, Any]) -> None:
    if not fetch_result:
        return
    basic_info = fetch_result.get("basic_info")
    if isinstance(basic_info, dict):
        record["basic_info"].update({k: v for k, v in basic_info.items() if v is not None})

    trend_history = fetch_result.get("trend_history")
    if isinstance(trend_history, dict):
        record["trend_history"] = trend_history

    posts = fetch_result.get("official_posts")
    if isinstance(posts, list):
        record["official_posts"][platform] = posts

    hot_reviews = fetch_result.get("hot_reviews")
    if isinstance(hot_reviews, list) and hot_reviews:
        record["hot_reviews"] = hot_reviews


def _align_trend_history(history: Dict[str, Any]) -> Dict[str, Any]:
    history = history or {}
    dates = list(history.get("dates") or [])
    reservations = list(history.get("reservations") or [])
    rating = list(history.get("rating") or [])

    # 对齐长度，缺失补 None，多余截断
    while len(reservations) < len(dates):
        reservations.append(None)
    while len(rating) < len(dates):
        rating.append(None)
    if len(reservations) > len(dates):
        reservations = reservations[: len(dates)]
    if len(rating) > len(dates):
        rating = rating[: len(dates)]

    return {"dates": dates, "reservations": reservations, "rating": rating}


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return None


def append_today_trend(record: Dict[str, Any]) -> None:
    """追加今日趋势数据，保留最近 30 天"""
    history = _align_trend_history(record.get("trend_history"))
    today_key = datetime.now().strftime("%m-%d")

    reservations_val = record.get("basic_info", {}).get("reservations")
    rating_raw = record.get("basic_info", {}).get("rating")
    rating_val = _to_float(rating_raw)
    rating_store = rating_val if rating_val is not None else rating_raw

    dates = history["dates"]
    reservations = history["reservations"]
    rating = history["rating"]

    if today_key in dates:
        idx = dates.index(today_key)
        reservations[idx] = reservations_val
        rating[idx] = rating_store
    else:
        dates.append(today_key)
        reservations.append(reservations_val)
        rating.append(rating_store)

    # 仅保留最近 30 条
    if len(dates) > 30:
        overflow = len(dates) - 30
        dates = dates[overflow:]
        reservations = reservations[overflow:]
        rating = rating[overflow:]

    record["trend_history"] = {
        "dates": dates,
        "reservations": reservations,
        "rating": rating,
    }


def _recalc_is_new(official_posts: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for platform, posts in (official_posts or {}).items():
        platform_posts: List[Dict[str, Any]] = []
        if isinstance(posts, list):
            for post in posts:
                if not isinstance(post, dict):
                    continue
                new_post = dict(post)
                new_post["is_new"] = is_current_week(post.get("date", ""))
                platform_posts.append(new_post)
        result[platform] = platform_posts
    return result


def handle_platform_fetch(platform: str, url: str, record: Dict[str, Any], old_record: Dict[str, Any]) -> None:
    fetcher = PLATFORM_FETCHERS.get(platform)
    if not fetcher:
        record["fetch_status"][platform] = "failed"
        return

    try:
        result = fetcher(url)
        if not result:
            # 约定空结果视为未实现/暂未配置，避免 stale 告警
            record["fetch_status"][platform] = "not_configured"
            return
        merge_fetch_result(record, platform, result)
        record["fetch_status"][platform] = "success"
    except Exception as exc:  # noqa: BLE001
        logging.exception("平台 %s 抓取异常，使用旧数据回退: %s", platform, exc)
        if old_record:
            record["fetch_status"][platform] = "stale"
            merge_fetch_result(record, platform, {
                "official_posts": old_record.get("official_posts", {}).get(platform, []),
            })
        else:
            record["fetch_status"][platform] = "failed"


def process_game(game_cfg: Dict[str, Any], old_record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    record = init_game_record(game_cfg, old_record)
    platforms_cfg = game_cfg.get("platforms", {}) or {}

    for platform in PLATFORMS:
        url = (platforms_cfg.get(platform) or {}).get("url")
        if not url:
            record["fetch_status"][platform] = "not_configured"
            continue

        # 简单防爬随机延迟（后续可扩展代理）
        random_delay_ms = random.randint(50, 200) / 1000.0
        # 使用 sleep 会减慢整体运行，后续可改为异步；框架先保留
        if random_delay_ms > 0:
            try:
                import time
                time.sleep(random_delay_ms)
            except Exception:
                pass

        handle_platform_fetch(platform, url, record, old_record or {})

    append_today_trend(record)
    record["basic_info"]["diffs"] = calculate_diffs(record["basic_info"], record.get("trend_history", {}))
    record["official_posts"] = _recalc_is_new(record.get("official_posts"))
    return record


def build_old_data_map(old_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in old_data:
        game_id = item.get("id")
        if game_id:
            result[game_id] = item
    return result


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )

    config = load_json(CONFIG_PATH, default=[])
    old_data = load_json(DATA_PATH, default=[])
    old_map = build_old_data_map(old_data if isinstance(old_data, list) else [])

    new_data: List[Dict[str, Any]] = []
    for game in config:
        if not game.get("enabled", False):
            continue
        game_id = game.get("id")
        if not game_id:
            logging.warning("跳过无 id 的配置项: %s", game)
            continue
        old_record = old_map.get(game_id)
        new_record = process_game(game, old_record)
        new_data.append(new_record)

    safe_write_json(DATA_PATH, new_data)
    logging.info("完成数据写入: %s", DATA_PATH)


if __name__ == "__main__":
    main()







