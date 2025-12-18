# -*- coding: utf-8 -*-
"""
TapTap 数据抓取模块
策略（简化版）：
1) 仅使用 HTML 文本正则，不依赖 JSON-LD
2) 兼容“预约/关注”与“安装/下载”字段差异
3) Rating 直接匹配纯数字（如 7.2）
"""
import logging
import os
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests

USER_AGENTS = [
    # 模拟常见安卓/桌面浏览器，提升返回完整页概率
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


def _headers() -> Dict[str, str]:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.taptap.cn/",
        "Origin": "https://www.taptap.cn",
    }
    cookie = os.getenv("TAPTAP_COOKIE")
    if cookie:
        headers["Cookie"] = cookie
    return headers


def _proxy() -> Optional[Dict[str, str]]:
    proxy = os.getenv("PROXY_URL")
    if proxy:
        return {"http": proxy, "https": proxy}
    return None


def _rand_delay():
    time.sleep(random.uniform(0.3, 0.9))


def _number(text: str) -> str:
    if not text:
        return "-"
    m = re.search(r"([\d\.]+\s*[万亿kK]?)", text)
    return m.group(1).replace(" ", "") if m else text.strip()


def _match_first(patterns, html: str) -> Optional[re.Match]:
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m
    return None


def _clean_text(text: str) -> str:
    return re.sub(r"<.*?>", "", text or "").strip()


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _parse_date(context: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", context)
    if m:
        return m.group(1)
    # “小时前/分钟前/天前”均视为当天
    if re.search(r"(分钟前|小时前|天前)", context):
        return _today_str()
    return _today_str()


def _to_float(text: str) -> Optional[float]:
    try:
        return float(text)
    except Exception:
        return None


def _extract_posts(html: str) -> List[Dict[str, object]]:
    posts: List[Dict[str, object]] = []
    for match in re.finditer(r'href="(https://www\.taptap\.cn/post/\d+)"[^>]*>(.*?)</a>', html):
        url = match.group(1)
        title = _clean_text(match.group(2))
        if not title:
            continue
        start = max(match.start() - 400, 0)
        end = min(match.end() + 400, len(html))
        ctx = html[start:end]

        date = _parse_date(ctx)
        comments_match = re.search(r"(评论|回复)[^\d]{0,5}(\d+)", ctx)
        likes_match = re.search(r"(点赞|喜欢|热度)[^\d]{0,5}(\d+)", ctx)

        posts.append(
            {
                "id": url.rsplit("/", 1)[-1],
                "title": title,
                "url": url,
                "date": date,
                "is_new": False,  # 后续自然周计算
                "comments": int(comments_match.group(2)) if comments_match else 0,
                "likes": int(likes_match.group(2)) if likes_match else 0,
            }
        )
        if len(posts) >= 10:
            break
    return posts


def _extract_reviews(html: str) -> List[Dict[str, object]]:
    reviews: List[Dict[str, object]] = []
    for match in re.finditer(r'href="(https://www\.taptap\.cn/review/\d+)"[^>]*>(.*?)</a>', html):
        url = match.group(1)
        content = _clean_text(match.group(2))
        if not content:
            continue
        start = max(match.start() - 400, 0)
        end = min(match.end() + 400, len(html))
        ctx = html[start:end]

        user_match = re.search(r'class="[^"]*(user|name)[^"]*">\s*([^<]{1,40})<', ctx)
        score_match = re.search(r"评分[^\d]{0,4}([0-5](?:\.\d)?)", ctx)
        likes_match = re.search(r"(点赞|喜欢)[^\d]{0,5}(\d+)", ctx)
        replies_match = re.search(r"(回复|评论)[^\d]{0,5}(\d+)", ctx)
        date = _parse_date(ctx)

        reviews.append(
            {
                "id": url.rsplit("/", 1)[-1],
                "platform": "taptap",
                "user": (user_match.group(2).strip() if user_match else ""),
                "content": content,
                "score": _to_float(score_match.group(1)) if score_match else None,
                "date": date,
                "likes": int(likes_match.group(2)) if likes_match else 0,
                "replies": int(replies_match.group(2)) if replies_match else 0,
                "is_new": False,
            }
        )
        if len(reviews) >= 5:
            break
    return reviews


def fetch_taptap_data(url: str) -> Dict[str, object]:
    if not url or "taptap.cn" not in url:
        return {}

    _rand_delay()

    def _fetch_with_retry() -> Optional[str]:
        delay = 0.6
        for attempt in range(3):
            try:
                resp = requests.get(
                    url,
                    headers=_headers(),
                    timeout=15,
                    proxies=_proxy(),
                    allow_redirects=True,
                )
                resp.raise_for_status()
                body = resp.text
                # 简单反爬探测：若正文包含下载 App / 请登录 等提示，视为失败
                lowered = body.lower()
                if any(key in lowered for key in ["下载 app", "login", "请登录", "captcha"]):
                    raise ValueError("suspect anti-bot page")
                return body
            except Exception as exc:
                logging.warning("TapTap 请求失败/疑似反爬 attempt=%s: %s", attempt + 1, exc)
                time.sleep(delay)
                delay *= 1.8
        return None

    html = _fetch_with_retry()
    if not html:
        return {}

    # Rating：匹配形如 >7.2< 或 data-rating="7.2"，兼容整数
    rating_match = _match_first(
        [
            r">([0-9]\.\d)<",
            r">([0-9])<",
            r'data-rating="([0-9]\.\d)"',
            r'"score"\s*:\s*([0-9]\.\d)',
        ],
        html,
    )
    rating = rating_match.group(1) if rating_match else "0.0"

    # 预约/安装/关注/评价
    reservations_match = _match_first(
        [
            r">([\d\.,万亿kK\s]+)\s*人?</span>[^<]{0,30}<span[^>]*>预约",
            r">([\d\.,万亿kK\s]+)\s*人?</span>[^<]{0,30}<span[^>]*>安装",
            r">([\d\.,万亿kK\s]+)\s*人?</span>[^<]{0,30}<span[^>]*>下载",
        ],
        html,
    )
    followers_match = _match_first(
        [
            r">([\d\.,万亿kK\s]+)\s*人?</span>[^<]{0,30}<span[^>]*>关注",
            r">([\d\.,万亿kK\s]+)\s*人?</span>[^<]{0,30}<span[^>]*>粉丝",
        ],
        html,
    )
    reviews_match = _match_first(
        [
            r">([\d\.,万亿kK\s]+)\s*条?</span>[^<]{0,30}<span[^>]*>评价",
            r'"reviewsCount"\s*:\s*([0-9\.eE\+]+)',
        ],
        html,
    )

    # 状态：已上线/预约中/敬请期待
    status = "未知"
    if re.search(r"(下载|安装)", html):
        status = "已上线"
    elif re.search(r"预约", html):
        status = "预约中"
    elif re.search(r"(敬请期待|即将上线)", html):
        status = "敬请期待"

    # 标签
    tags = re.findall(r'<a[^>]*class="[^"]*tag[^"]*"[^>]*>(.*?)</a>', html)
    tags = [re.sub(r"<.*?>", "", t).strip() for t in tags if t.strip()]
    if not tags:
        meta_kw = re.search(r'<meta name="keywords" content="(.*?)">', html)
        if meta_kw:
            tags = [x.strip() for x in meta_kw.group(1).split(",") if x.strip()]

    basic_info = {
        "status": status,
        "rating": _to_float(rating) if rating else None,
        "reservations": _number(reservations_match.group(1)) if reservations_match else "-",
        "followers": _number(followers_match.group(1)) if followers_match else "-",
        "review_count": _number(reviews_match.group(1)) if reviews_match else "-",
        "tags": tags[:5],
        "diffs": {},
    }

    return {
        "basic_info": basic_info,
        "official_posts": _extract_posts(html),
        "hot_reviews": _extract_reviews(html),
        "trend_history": {},
    }


