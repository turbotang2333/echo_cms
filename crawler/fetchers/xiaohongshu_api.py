# -*- coding: utf-8 -*-
"""
小红书数据抓取模块（API 方式）
基于 Spider_XHS 项目的实现
参考：https://github.com/cv-cat/Spider_XHS
"""
from __future__ import annotations

import json
import logging
import math
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import execjs
    import requests
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    logging.warning("缺少依赖：pip install PyExecJS requests")


def generate_x_b3_traceid(length=16) -> str:
    """生成 x-b3-traceid"""
    chars = "abcdef0123456789"
    return ''.join(chars[math.floor(16 * random.random())] for _ in range(length))


def trans_cookies(cookies_str: str) -> Dict[str, str]:
    """将 Cookie 字符串转换为字典"""
    cookies = {}
    for item in cookies_str.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies[name.strip()] = value.strip()
    return cookies


def load_js_sign() -> Optional[Any]:
    """加载 JavaScript 签名算法"""
    js_path = Path(__file__).resolve().parent.parent / "xhs_sign.js"
    if not js_path.exists():
        logging.error("签名文件不存在: %s", js_path)
        return None
    
    try:
        with js_path.open("r", encoding="utf-8") as f:
            js_code = f.read()
        return execjs.compile(js_code)
    except Exception as e:
        logging.error("加载签名文件失败: %s", e)
        return None


def generate_headers(a1: str, api: str, data: Any = '', method: str = 'POST') -> tuple:
    """
    生成请求头
    
    Args:
        a1: Cookie 中的 a1 值
        api: API 路径
        data: 请求数据
        method: 请求方法
        
    Returns:
        (headers, data_str)
    """
    js = load_js_sign()
    if not js:
        return {}, ''
    
    try:
        # 调用 JS 函数生成签名
        ret = js.call('get_request_headers_params', api, data, a1, method)
        xs, xt, xs_common = ret['xs'], ret['xt'], ret['xs_common']
        
        # 构建请求头
        headers = {
            "authority": "edith.xiaohongshu.com",
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://www.xiaohongshu.com",
            "pragma": "no-cache",
            "referer": "https://www.xiaohongshu.com/",
            "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="131", "Chromium";v="131"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "x-b3-traceid": generate_x_b3_traceid(),
            "x-s": xs,
            "x-t": str(xt),
            "x-s-common": xs_common,
        }
        
        # 转换数据为 JSON 字符串
        if data:
            data = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        
        return headers, data
    except Exception as e:
        logging.error("生成请求头失败: %s", e)
        return {}, ''


def extract_user_id(url: str) -> Optional[str]:
    """从小红书 URL 提取 user_id"""
    match = re.search(r'/user/profile/([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None


def fetch_xiaohongshu_data(url: str) -> Dict[str, Any]:
    """
    抓取小红书用户数据（API 方式）
    
    Args:
        url: 小红书用户主页 URL
        
    Returns:
        包含 basic_info, official_posts 的字典
    """
    if not DEPENDENCIES_AVAILABLE:
        logging.error("缺少依赖库，无法使用 API 方式抓取")
        return {}
    
    user_id = extract_user_id(url)
    if not user_id:
        logging.error("无法从 URL 提取 user_id: %s", url)
        return {}
    
    # 从环境变量加载 Cookie
    import os
    cookie_str = os.getenv("XIAOHONGSHU_COOKIE", "")
    if not cookie_str:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("XIAOHONGSHU_COOKIE="):
                        cookie_str = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    
    if not cookie_str or cookie_str == "your_cookie_here":
        logging.error("Cookie 未配置")
        return {}
    
    cookies = trans_cookies(cookie_str)
    a1 = cookies.get('a1')
    if not a1:
        logging.error("Cookie 中缺少 a1 参数")
        return {}
    
    result: Dict[str, Any] = {
        "basic_info": {},
        "official_posts": [],
    }
    
    base_url = "https://edith.xiaohongshu.com"
    
    try:
        # 1. 获取用户信息
        logging.info("正在获取用户信息: %s", user_id)
        api = f"/api/sns/web/v1/user/otherinfo?target_user_id={user_id}"
        headers, _ = generate_headers(a1, api, '', 'GET')
        
        logging.debug("请求 URL: %s%s", base_url, api)
        logging.debug("Cookie a1: %s", a1[:20] + "...")
        logging.debug("Cookies 数量: %d", len(cookies))
        logging.debug("请求头 x-s: %s", headers.get('x-s', '')[:30] + "...")
        
        # 确保所有 Cookie 都传递
        session = requests.Session()
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.xiaohongshu.com', path='/')
        
        response = session.get(base_url + api, headers=headers, timeout=30)
        logging.debug("响应状态码: %s", response.status_code)
        logging.debug("响应内容: %s", response.text[:200])
        user_data = response.json()
        
        if user_data.get("success"):
            data = user_data.get("data", {})
            user_info = data.get("basic_info", {})
            
            # 从 interactions 数组提取粉丝数、关注数、获赞数
            interactions = data.get("interactions", [])
            xhs_following = "0"
            xhs_followers = "0"
            xhs_likes = "0"
            for item in interactions:
                if item.get("type") == "follows":
                    xhs_following = str(item.get("count", "0"))
                elif item.get("type") == "fans":
                    xhs_followers = str(item.get("count", "0"))
                elif item.get("type") == "interaction":
                    xhs_likes = str(item.get("count", "0"))
            
            result["basic_info"] = {
                "xhs_following": xhs_following,
                "xhs_followers": xhs_followers,
                "xhs_likes": xhs_likes,
                "user_name": user_info.get("nickname", ""),
            }
            logging.info("用户信息: %s, 粉丝 %s, 获赞 %s", 
                        result["basic_info"].get("user_name"),
                        result["basic_info"].get("xhs_followers"),
                        result["basic_info"].get("xhs_likes"))
        else:
            logging.error("获取用户信息失败: %s", user_data.get("msg"))
            return result
        
        # 2. 获取用户笔记列表
        logging.info("正在获取用户笔记列表")
        api = f"/api/sns/web/v1/user_posted?num=30&cursor=&user_id={user_id}&image_formats=jpg,webp,avif"
        headers, _ = generate_headers(a1, api, '', 'GET')
        
        response = session.get(base_url + api, headers=headers, timeout=30)
        notes_data = response.json()
        
        if notes_data.get("success"):
            notes = notes_data.get("data", {}).get("notes", [])
            posts = []
            
            for note in notes:
                # 跳过置顶笔记
                interact_info = note.get("interact_info", {})
                if interact_info.get("sticky"):
                    logging.debug("跳过置顶笔记: %s", note.get("display_title", "")[:20])
                    continue
                
                note_id = note.get("note_id", "")
                title = note.get("display_title", "") or note.get("title", "") or note.get("desc", "")
                
                # 点赞数
                likes = interact_info.get("liked_count", "0")
                
                posts.append({
                    "id": note_id,
                    "title": title[:50] if title else "无标题",
                    "url": f"https://www.xiaohongshu.com/explore/{note_id}",
                    "date": "",  # API 不返回发布时间
                    "is_new": False,
                    "likes": str(likes),
                    "comments": "0",  # API 不返回评论数
                })
                
                if len(posts) >= 5:
                    break
            
            result["official_posts"] = posts
            logging.info("获取到 %d 条非置顶笔记", len(posts))
        else:
            logging.error("获取笔记列表失败: %s", notes_data.get("msg"))
        
    except requests.exceptions.Timeout:
        logging.error("请求超时")
    except Exception as e:
        logging.exception("抓取失败: %s", e)
    
    return result


# 用于独立测试
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    test_urls = [
        "https://www.xiaohongshu.com/user/profile/6805bb4c000000000e011c20",  # 夜幕之下
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"测试 URL: {url}")
        print('='*60)
        result = fetch_xiaohongshu_data(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))

