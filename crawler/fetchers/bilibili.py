# -*- coding: utf-8 -*-
"""
B站数据抓取模块（API 方式）
使用 Cookie + API 直接调用B站接口
参考 MediaCrawler 项目的实现方式
"""
from __future__ import annotations

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
    """从B站 URL 提取 uid"""
    # 支持格式：https://space.bilibili.com/3546889188280924
    match = re.search(r'/space\.bilibili\.com/(\d+)', url)
    if match:
        return match.group(1)
    
    # 直接提取数字
    match = re.search(r'/(\d{10,})', url)
    return match.group(1) if match else None


def format_number(num: Any) -> str:
    """格式化数字（保留万为单位）"""
    if not num:
        return "0"
    
    try:
        # 如果已经是字符串格式（如 "1.2万"）
        if isinstance(num, str):
            if '万' in num or '亿' in num:
                return num
            num = int(num.replace(',', ''))
        
        num = int(num)
        if num >= 10000:
            return f"{num / 10000:.1f}万"
        return str(num)
    except (ValueError, TypeError):
        return str(num)


def get_user_relation(uid: str, cookies: Dict[str, str], session: requests.Session) -> Dict[str, Any]:
    """
    获取B站用户关系统计（粉丝数、关注数等）
    
    Args:
        uid: B站用户ID
        cookies: Cookie字典
        session: requests.Session 对象
        
    Returns:
        关系统计信息
    """
    api_url = f"https://api.bilibili.com/x/relation/stat?vmid={uid}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://space.bilibili.com/{uid}/",
        "Origin": "https://space.bilibili.com",
    }
    
    try:
        response = session.get(api_url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0:
            return data.get("data", {})
        else:
            logging.warning("获取用户关系统计失败: %s", data.get("message"))
            return {}
            
    except requests.exceptions.Timeout:
        logging.error("获取用户关系统计超时")
        return {}
    except Exception as e:
        logging.exception("获取用户关系统计失败: %s", e)
        return {}


def get_user_upstat(uid: str, cookies: Dict[str, str], session: requests.Session) -> Dict[str, Any]:
    """
    获取B站UP主统计信息（获赞数、播放数等）
    
    Args:
        uid: B站用户ID
        cookies: Cookie字典
        session: requests.Session 对象
        
    Returns:
        UP主统计信息
    """
    api_url = f"https://api.bilibili.com/x/space/upstat?mid={uid}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://space.bilibili.com/{uid}/",
        "Origin": "https://space.bilibili.com",
    }
    
    try:
        response = session.get(api_url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == 0:
            return data.get("data", {})
        else:
            logging.warning("获取UP主统计失败: %s", data.get("message"))
            return {}
            
    except requests.exceptions.Timeout:
        logging.error("获取UP主统计超时")
        return {}
    except Exception as e:
        logging.exception("获取UP主统计失败: %s", e)
        return {}


def get_user_dynamics(uid: str, cookies: Dict[str, str], session: requests.Session) -> List[Dict[str, Any]]:
    """
    获取B站用户动态列表
    
    Args:
        uid: B站用户ID
        cookies: Cookie字典
        session: requests.Session 对象
        
    Returns:
        动态列表
    """
    api_url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={uid}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": f"https://space.bilibili.com/{uid}/dynamic",
        "Origin": "https://space.bilibili.com",
    }
    
    try:
        response = session.get(api_url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            logging.warning("获取动态列表失败: %s", data.get("message"))
            return []
        
        items = data.get("data", {}).get("items", [])
        dynamics = []
        now = datetime.now()
        
        for item in items:
            if len(dynamics) >= 5:  # 只取前5条
                break
                
            modules = item.get("modules", {})
            
            # 提取内容 - 从 module_dynamic 的 major 字段
            content = ""
            desc_module = modules.get("module_dynamic", {})
            
            if desc_module:
                # 1. 尝试从 desc.text 获取（纯文本动态）
                desc = desc_module.get("desc")
                if desc and isinstance(desc, dict):
                    content = desc.get("text", "")
                
                # 2. 从 major 字段获取（图文、文章等）
                if not content:
                    major = desc_module.get("major", {})
                    major_type = major.get("type", "")
                    
                    if major_type == "MAJOR_TYPE_ARTICLE":
                        # 文章类型
                        article = major.get("article", {})
                        content = article.get("title", "")
                    elif major_type == "MAJOR_TYPE_DRAW":
                        # 图文类型 - 尝试从 additional 获取关联信息
                        additional = desc_module.get("additional", {})
                        common = additional.get("common", {}) if additional else {}
                        
                        if common and common.get("title"):
                            # 如果有关联游戏/内容，显示它
                            game_title = common.get("title", "")
                            content = f"发布了《{game_title}》相关图文"
                        else:
                            # 纯图文动态
                            content = "发布了图文动态"
                    elif major_type == "MAJOR_TYPE_ARCHIVE":
                        # 视频类型
                        archive = major.get("archive", {})
                        content = archive.get("title", "")
                    elif major_type == "MAJOR_TYPE_OPUS":
                        # 图文动态（新版）
                        opus = major.get("opus", {})
                        summary = opus.get("summary", {})
                        content = summary.get("text", "发布了图文动态")
            
            # 如果还是没有内容，跳过
            if not content or len(content) < 2:
                continue
            
            # 提取时间
            author = modules.get("module_author", {})
            pub_ts = author.get("pub_ts", 0)
            try:
                # 确保 pub_ts 是整数
                pub_ts = int(pub_ts) if pub_ts else 0
                if pub_ts:
                    pub_time = datetime.fromtimestamp(pub_ts)
                    date_str = f"{pub_time.month}/{pub_time.day}"
                    is_new = (now - pub_time).days <= 7
                else:
                    date_str = ""
                    is_new = False
            except (ValueError, TypeError, OSError):
                date_str = ""
                is_new = False
            
            # 提取统计数据
            stat = modules.get("module_stat", {})
            likes = stat.get("like", {}).get("count", 0)
            comments = stat.get("comment", {}).get("count", 0)
            reposts = stat.get("forward", {}).get("count", 0)
            
            dynamics.append({
                "title": content[:50],
                "date": date_str,
                "likes": str(likes),
                "comments": str(comments),
                "reposts": str(reposts),
                "is_new": is_new,
            })
        
        return dynamics
        
    except requests.exceptions.Timeout:
        logging.error("获取动态列表超时")
        return []
    except Exception as e:
        logging.exception("获取动态列表失败: %s", e)
        return []


def fetch_bilibili_data(url: str) -> Dict[str, Any]:
    """
    抓取B站用户数据（API 方式）
    
    Args:
        url: B站用户主页 URL，如 https://space.bilibili.com/3546889188280924
        
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
    cookie_str = os.getenv("BILIBILI_COOKIE", "")
    if not cookie_str:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("BILIBILI_COOKIE="):
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
        # 1. 获取用户关系统计（粉丝数等）
        logging.info("正在获取用户关系统计: %s", uid)
        relation_stat = get_user_relation(uid, cookies, session)
        
        # 2. 获取UP主统计（获赞数等）
        logging.info("正在获取UP主统计")
        upstat = get_user_upstat(uid, cookies, session)
        
        # 组装基础信息
        follower = relation_stat.get("follower", 0)
        likes = upstat.get("likes", 0)
        
        result["basic_info"] = {
            "bili_followers": format_number(follower),
            "bili_likes": format_number(likes),
        }
        
        logging.info("用户信息: 粉丝 %s, 获赞 %s", 
                    result["basic_info"].get("bili_followers"),
                    result["basic_info"].get("bili_likes"))
        
        # 短暂延迟，避免请求过快
        time.sleep(1)
        
        # 3. 获取动态列表
        logging.info("正在获取动态列表")
        dynamics = get_user_dynamics(uid, cookies, session)
        result["official_posts"] = dynamics
        
        if dynamics:
            logging.info("获取到 %d 条动态", len(dynamics))
        
    except Exception as e:
        logging.exception("抓取B站数据失败: %s", e)
    finally:
        session.close()
    
    return result


# 用于独立测试
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    test_urls = [
        "https://space.bilibili.com/3546889188280924",  # 测试账号
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"测试 URL: {url}")
        print('='*60)
        result = fetch_bilibili_data(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
