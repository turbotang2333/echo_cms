# -*- coding: utf-8 -*-
"""
微博数据抓取模块（移动版API方式）
使用微博移动版 API 抓取用户数据
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    logging.warning("缺少依赖：pip install requests")


def trans_cookies(cookies_str: str) -> Dict[str, str]:
    """将 Cookie 字符串转换为字典"""
    cookies = {}
    for item in cookies_str.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies[name.strip()] = value.strip()
    return cookies


def extract_uid(url: str) -> Optional[str]:
    """从微博 URL 提取 uid"""
    # 支持格式1：https://weibo.com/u/7994214945
    match = re.search(r'/u/(\d+)', url)
    if match:
        return match.group(1)
    
    # 支持格式2：https://weibo.com/7994214945
    match = re.search(r'weibo\.com/(\d+)', url)
    if match:
        return match.group(1)
    
    return None


def format_number(num: Any) -> str:
    """格式化数字（保留万为单位）"""
    if not num:
        return "0"
    
    try:
        num = int(num)
        if num >= 10000:
            return f"{num / 10000:.1f}万"
        return str(num)
    except (ValueError, TypeError):
        return str(num)


def parse_weibo_time(created_at: str) -> str:
    """
    解析微博时间为 MM/DD 格式
    
    Args:
        created_at: 微博时间字符串，如 "Wed Dec 25 10:30:00 +0800 2024"
        
    Returns:
        格式化的日期字符串，如 "12/25"
    """
    try:
        # 微博时间格式: "Wed Dec 25 10:30:00 +0800 2024"
        dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        return f"{dt.month}/{dt.day}"
    except Exception as e:
        logging.warning("解析时间失败: %s, 原始值: %s", e, created_at)
        return ""


def is_this_week(created_at: str) -> bool:
    """判断微博是否发布于本周（自然周，周一到周日）"""
    try:
        dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        now = datetime.now()
        
        # 计算本周一的日期
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 移除时区信息进行比较
        dt_naive = dt.replace(tzinfo=None)
        
        return dt_naive >= week_start
    except Exception:
        return False


def get_user_info(uid: str, cookies: Dict[str, str], session: requests.Session) -> Dict[str, Any]:
    """
    获取微博用户基础信息
    
    Args:
        uid: 微博用户ID
        cookies: Cookie字典
        session: requests.Session 对象
        
    Returns:
        用户信息字典
    """
    api_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Referer": "https://m.weibo.cn/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    try:
        response = session.get(api_url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("ok") != 1:
            logging.error("获取用户信息失败: %s", data.get("msg", "未知错误"))
            return {}
        
        userInfo = data.get("data", {}).get("userInfo", {})
        
        # 提取粉丝数
        followers_count = userInfo.get("followers_count", 0)
        
        return {
            "wb_followers": format_number(followers_count),
            "user_name": userInfo.get("screen_name", ""),
        }
        
    except requests.exceptions.Timeout:
        logging.error("获取用户信息超时")
        return {}
    except Exception as e:
        logging.exception("获取用户信息失败: %s", e)
        return {}


def get_user_posts(uid: str, cookies: Dict[str, str], session: requests.Session) -> List[Dict[str, Any]]:
    """
    获取微博用户的微博列表（排除置顶）
    
    Args:
        uid: 微博用户ID
        cookies: Cookie字典
        session: requests.Session 对象
        
    Returns:
        微博列表
    """
    # containerid 格式：107603 + uid
    containerid = f"107603{uid}"
    api_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid={containerid}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        "Referer": f"https://m.weibo.cn/u/{uid}",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    try:
        response = session.get(api_url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("ok") != 1:
            logging.error("获取微博列表失败: %s", data.get("msg", "未知错误"))
            return []
        
        cards = data.get("data", {}).get("cards", [])
        posts = []
        
        for card in cards:
            # 只处理微博类型的卡片
            if card.get("card_type") != 9:
                continue
            
            mblog = card.get("mblog", {})
            if not mblog:
                continue
            
            # 跳过置顶微博
            title_data = mblog.get("title", {})
            if isinstance(title_data, dict) and title_data.get("text") == "置顶":
                logging.debug("跳过置顶微博")
                continue
            
            # 提取微博正文（去除HTML标签）
            text_raw = mblog.get("text", "")
            text = re.sub(r'<[^>]+>', '', text_raw)  # 移除HTML标签
            text = text.strip()
            
            # 如果是转发微博，尝试获取原创内容
            if mblog.get("retweeted_status"):
                # 转发微博使用 "转发了xxx的微博" 这类文本
                text = text[:50] if text else "转发微博"
            else:
                text = text[:50] if text else "无文字内容"
            
            # 提取互动数据
            reposts_count = mblog.get("reposts_count", 0)
            comments_count = mblog.get("comments_count", 0)
            attitudes_count = mblog.get("attitudes_count", 0)  # 点赞数
            
            # 提取发布时间
            created_at = mblog.get("created_at", "")
            date_str = parse_weibo_time(created_at)
            
            # 判断是否本周新微博
            is_new = is_this_week(created_at)
            
            posts.append({
                "id": mblog.get("id", ""),
                "title": text,
                "date": date_str,
                "is_new": is_new,
                "reposts": str(reposts_count),
                "comments": str(comments_count),
                "likes": str(attitudes_count),
            })
            
            # 只取前5条非置顶微博
            if len(posts) >= 5:
                break
        
        return posts
        
    except requests.exceptions.Timeout:
        logging.error("获取微博列表超时")
        return []
    except Exception as e:
        logging.exception("获取微博列表失败: %s", e)
        return []


def fetch_weibo_data(url: str) -> Dict[str, Any]:
    """
    抓取微博用户数据（移动版API方式）
    
    Args:
        url: 微博用户主页 URL，如 https://weibo.com/u/7994214945
        
    Returns:
        包含 basic_info, official_posts 的字典
    """
    if not DEPENDENCIES_AVAILABLE:
        logging.error("缺少依赖库，无法使用 API 方式抓取")
        return {}
    
    uid = extract_uid(url)
    if not uid:
        logging.error("无法从 URL 提取 uid: %s", url)
        return {}
    
    # 从环境变量加载 Cookie
    import os
    cookie_str = os.getenv("WEIBO_COOKIE", "")
    if not cookie_str:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("WEIBO_COOKIE="):
                        cookie_str = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    
    if not cookie_str or cookie_str == "your_cookie_here":
        logging.error("Cookie 未配置")
        return {}
    
    cookies = trans_cookies(cookie_str)
    
    result: Dict[str, Any] = {
        "basic_info": {},
        "official_posts": [],
    }
    
    # 创建 Session 复用连接
    session = requests.Session()
    
    try:
        # 1. 获取用户基础信息
        logging.info("正在获取微博用户信息: %s", uid)
        user_info = get_user_info(uid, cookies, session)
        result["basic_info"] = user_info
        
        if user_info:
            logging.info("用户信息: %s, 粉丝 %s", 
                        user_info.get("user_name", ""),
                        user_info.get("wb_followers", "0"))
        
        # 短暂延迟，避免请求过快
        time.sleep(1)
        
        # 2. 获取微博列表
        logging.info("正在获取微博列表")
        posts = get_user_posts(uid, cookies, session)
        result["official_posts"] = posts
        
        if posts:
            logging.info("获取到 %d 条非置顶微博", len(posts))
        
    except Exception as e:
        logging.exception("抓取微博数据失败: %s", e)
    finally:
        session.close()
    
    return result


# 用于独立测试
if __name__ == "__main__":
    import json
    from datetime import timedelta
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    test_urls = [
        "https://weibo.com/u/7994214945",  # 测试账号
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"测试 URL: {url}")
        print('='*60)
        result = fetch_weibo_data(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))

