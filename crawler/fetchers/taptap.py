# -*- coding: utf-8 -*-
"""
TapTap 数据抓取模块
使用 Playwright 浏览器自动化提取数据
需要访问 3 个页面：基础数据页、官方帖子页、热门评论页
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


def convert_relative_time(relative_time: str, fetch_time: datetime = None) -> str:
    """
    把相对时间转换为绝对日期
    
    Args:
        relative_time: 如 "2天前"、"19小时前"、"修改于 2025/12/1"
        fetch_time: 爬取时间，默认为当前时间
        
    Returns:
        格式化的日期字符串，如 "12/16" 或 "12/1"
    """
    if not relative_time:
        return ""
    
    fetch_time = fetch_time or datetime.now()
    
    # 已经是绝对日期格式
    if "修改于" in relative_time:
        match = re.search(r'(\d{4})/(\d+)/(\d+)', relative_time)
        if match:
            return f"{match.group(2)}/{match.group(3)}"
        return relative_time.replace("修改于 ", "")
    
    # 绝对日期格式
    match = re.match(r'(\d{4})/(\d+)/(\d+)', relative_time)
    if match:
        return f"{match.group(2)}/{match.group(3)}"
    
    # 相对时间转换
    if "分钟前" in relative_time:
        minutes = int(re.search(r'(\d+)', relative_time).group(1))
        result_date = fetch_time - timedelta(minutes=minutes)
    elif "小时前" in relative_time:
        hours = int(re.search(r'(\d+)', relative_time).group(1))
        result_date = fetch_time - timedelta(hours=hours)
    elif "天前" in relative_time:
        days = int(re.search(r'(\d+)', relative_time).group(1))
        result_date = fetch_time - timedelta(days=days)
    else:
        return relative_time
    
    return f"{result_date.month}/{result_date.day}"

try:
    from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright 未安装，TapTap 抓取功能不可用。请运行: pip install playwright && playwright install chromium")


def extract_app_id(url: str) -> Optional[str]:
    """从 TapTap URL 提取 app_id"""
    match = re.search(r'/app/(\d+)', url)
    return match.group(1) if match else None


def extract_basic_info(page: Page) -> Dict[str, Any]:
    """从基础数据页提取信息"""
    js_code = """
    () => {
        const data = {};
        
        // 游戏名称
        data.name = document.querySelector('h1')?.textContent?.trim() || '';
        
        const text = document.body.innerText;
        
        // 评分 - 匹配如 "9.3" 在 "官方入驻" 或 "安卓" 之前
        const ratingMatch = text.match(/(\\d\\.\\d)\\s*(?:官方入驻|安卓)/);
        data.rating = ratingMatch ? ratingMatch[1] : '';
        
        // 预约数 - 优先匹配 "104 万" 格式，然后是 "6.7万人预约"
        const reserveMatch1 = text.match(/预约\\s*(\\d+(?:\\.\\d+)?)\\s*万/);
        const reserveMatch2 = text.match(/(\\d+(?:\\.\\d+)?)\\s*万?人?预约/);
        if (reserveMatch1) {
            data.reservations = reserveMatch1[1] + '万';
        } else if (reserveMatch2) {
            data.reservations = reserveMatch2[1] + '万';
        } else {
            data.reservations = '-';
        }
        
        // 关注数 - 匹配 "关注 109 万" 格式
        const followMatch1 = text.match(/关注\\s*(\\d+(?:\\.\\d+)?)\\s*万/);
        const followMatch2 = text.match(/(\\d+(?:\\.\\d+)?)\\s*万?人?关注/);
        if (followMatch1) {
            data.followers = followMatch1[1] + '万';
        } else if (followMatch2) {
            data.followers = followMatch2[1] + '万';
        } else {
            data.followers = '-';
        }
        
        // 评价数
        const reviewMatch = text.match(/评价\\s*(\\d+(?:\\.\\d+)?\\s*万?)\\s*条/) || 
                           text.match(/(\\d+(?:\\.\\d+)?\\s*万?)\\s*(?:个)?评价/);
        data.review_count = reviewMatch ? reviewMatch[1] : '0';
        
        // 标签
        const tagLinks = document.querySelectorAll('a[href*="/tag/"]');
        data.tags = [...new Set([...tagLinks].map(a => a.textContent.trim()).filter(t => t && t.length < 10))].slice(0, 5);
        
        // 开发商 - 查找页面上的开发商名称
        // 通常在详情页有 "开发xxx" 或开发商单独一行
        data.developer = '';
        const devPatterns = [
            /开发([\\u4e00-\\u9fa5]+(?:工作室|游戏|科技|网络|娱乐|互动))/,
            /厂商([\\u4e00-\\u9fa5]+)/,
        ];
        for (const pattern of devPatterns) {
            const match = text.match(pattern);
            if (match && match[1] && !match[1].includes('者中心')) {
                data.developer = match[1];
                break;
            }
        }
        
        // 评价数去除空格
        data.review_count = data.review_count.trim();
        
        // 状态判断
        if (text.includes('预约')) {
            data.status = '预约中';
        } else if (text.includes('测试')) {
            data.status = '测试中';
        } else {
            data.status = '已上线';
        }
        
        return data;
    }
    """
    try:
        result = page.evaluate(js_code)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        logging.error("提取基础数据失败: %s", e)
        return {}


def extract_official_posts(page: Page) -> List[Dict[str, Any]]:
    """从官方帖子页提取信息（基于DOM结构）"""
    js_code = """
    () => {
        const posts = [];
        const seen = new Set();
        
        // 方法1：查找帖子卡片（通过日期格式定位）
        const text = document.body.innerText;
        const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
        
        // 找到所有日期行的索引
        const dateIndices = [];
        lines.forEach((line, idx) => {
            if (line.match(/^(2025|2024)\\/\\d+\\/\\d+$/)) {
                dateIndices.push(idx);
            }
        });
        
        // 对每个日期，向下查找标题和统计数据
        for (const dateIdx of dateIndices) {
            if (posts.length >= 5) break;
            
            const date = lines[dateIdx];
            
            // 向下查找标题（日期后面的第一个较长文本）
            let title = '';
            for (let j = dateIdx + 1; j < Math.min(dateIdx + 5, lines.length); j++) {
                const line = lines[j];
                // 标题特征：长度适中，不是纯数字，不是"综合"等标签
                if (line.length >= 8 && line.length <= 100 && 
                    !line.match(/^\\d+$/) && 
                    !['综合', '官方', '精华', '视频', '回复时间', '加载中'].includes(line)) {
                    title = line;
                    break;
                }
            }
            
            if (!title) continue;
            
            // 去重
            const titleKey = title.substring(0, 30);
            if (seen.has(titleKey)) continue;
            seen.add(titleKey);
            
            // 查找统计数据（日期附近的数字）
            let comments = '0', likes = '0';
            let foundStats = 0;
            
            // 先向上查找（有些布局数字在日期上方）
            for (let j = dateIdx - 1; j >= Math.max(0, dateIdx - 10) && foundStats < 2; j--) {
                if (lines[j].match(/^\\d+$/)) {
                    if (foundStats === 0) likes = lines[j];
                    else comments = lines[j];
                    foundStats++;
                }
            }
            
            // 如果上方没找到，向下查找
            if (foundStats === 0) {
                for (let j = dateIdx + 1; j < Math.min(dateIdx + 15, lines.length) && foundStats < 2; j++) {
                    if (lines[j].match(/^\\d+$/)) {
                        if (foundStats === 0) comments = lines[j];
                        else likes = lines[j];
                        foundStats++;
                    }
                }
            }
            
            // 判断是否本周新帖
            const postDate = new Date(date.replace(/\\//g, '-'));
            const now = new Date();
            const weekStart = new Date(now);
            weekStart.setDate(now.getDate() - now.getDay() + 1); // 本周一
            weekStart.setHours(0, 0, 0, 0);
            const is_new = postDate >= weekStart;
            
            posts.push({ title, date, comments, likes, is_new });
        }
        
        return posts;
    }
    """
    try:
        result = page.evaluate(js_code)
        return result if isinstance(result, list) else []
    except Exception as e:
        logging.error("提取官方帖子失败: %s", e)
        return []


def extract_hot_reviews(page: Page, fetch_time: datetime = None) -> List[Dict[str, Any]]:
    """从评论页提取信息（按页面显示顺序）"""
    fetch_time = fetch_time or datetime.now()
    
    js_code = """
    () => {
        const reviews = [];
        const seenHrefs = new Set();
        
        // 按 DOM 顺序遍历评论链接
        document.querySelectorAll('a[href^="/review/"]').forEach(link => {
            const href = link.getAttribute('href');
            if (!href || !href.match(/^\\/review\\/\\d+$/) || seenHrefs.has(href)) return;
            
            const content = link.textContent.trim();
            if (content.length < 15) return;
            
            seenHrefs.add(href);
            
            // 向上查找最小的包含用户信息的父容器（避免范围过大）
            let card = link.parentElement;
            let found = false;
            
            for (let i = 0; i < 5; i++) {
                if (!card) break;
                
                const userLinks = card.querySelectorAll('a[href^="/user/"]');
                if (userLinks.length >= 1) {
                    // 找第一个有文本的用户链接作为评论者
                    let userName = '';
                    for (const u of userLinks) {
                        const t = u.textContent.trim();
                        if (t && t.length > 0 && t.length < 30) {
                            userName = t;
                            break;
                        }
                    }
                    
                    if (userName) {
                        // 提取时间
                        const timeMatch = card.innerText.match(/(\\d+\\s*(?:小时|天|分钟)前|修改于\\s*\\d+\\/\\d+\\/\\d+|\\d{4}\\/\\d+\\/\\d+)/);
                        const rawTime = timeMatch ? timeMatch[0] : '';
                        
                        // 提取回复数和点赞数
                        let replies = '0', likes = '0';
                        const replyLink = card.querySelector('a[href$="#to-reply"]');
                        if (replyLink) {
                            const replyText = replyLink.textContent.trim();
                            if (replyText && /^\\d+$/.test(replyText)) {
                                replies = replyText;
                            }
                        }
                        // 点赞数通常在回复数后面
                        const allNums = card.innerText.match(/\\d+/g) || [];
                        if (allNums.length >= 2) {
                            const lastTwo = allNums.slice(-2);
                            if (!replies || replies === '0') replies = lastTwo[0];
                            likes = lastTwo[1];
                        }
                        
                        // 评分：通过前景层宽度比例计算
                        let score = 5;
                        let bgWidth = 0, fgWidth = 0;
                        card.querySelectorAll('div').forEach(div => {
                            const stars = div.querySelectorAll(':scope > .review-rate__star');
                            if (stars.length === 5) {
                                const style = getComputedStyle(div);
                                const rect = div.getBoundingClientRect();
                                if (style.position === 'absolute' && style.overflow === 'hidden') {
                                    fgWidth = rect.width;
                                } else if (rect.width > 0) {
                                    bgWidth = rect.width;
                                }
                            }
                        });
                        if (bgWidth > 0 && fgWidth > 0) {
                            score = Math.round((fgWidth / bgWidth) * 5);
                            if (score < 1) score = 1;
                            if (score > 5) score = 5;
                        }
                        
                        reviews.push({
                            user: userName,
                            content: content.substring(0, 100),
                            score: score,
                            rawTime: rawTime,
                            likes: likes,
                            replies: replies,
                            is_new: false
                        });
                        found = true;
                        break;
                    }
                }
                card = card.parentElement;
            }
        });
        
        return reviews.slice(0, 5);
    }
    """
    try:
        result = page.evaluate(js_code)
        if not isinstance(result, list):
            return []
        
        # 转换时间格式
        for review in result:
            raw_time = review.pop('rawTime', '')
            review['time'] = convert_relative_time(raw_time, fetch_time)
        
        return result
    except Exception as e:
        logging.error("提取热门评论失败: %s", e)
        return []


def fetch_taptap_data(url: str) -> Dict[str, Any]:
    """
    抓取 TapTap 游戏数据
    
    Args:
        url: TapTap 游戏主页 URL，如 https://www.taptap.cn/app/786394?os=android
        
    Returns:
        包含 basic_info, official_posts, hot_reviews 的字典
    """
    if not PLAYWRIGHT_AVAILABLE:
        logging.error("Playwright 未安装，无法抓取 TapTap 数据")
        return {}
    
    app_id = extract_app_id(url)
    if not app_id:
        logging.error("无法从 URL 提取 app_id: %s", url)
        return {}
    
    # 构建三个页面的 URL
    base_url = f"https://www.taptap.cn/app/{app_id}?os=android"
    posts_url = f"https://www.taptap.cn/app/{app_id}/topic?type=official"
    reviews_url = f"https://www.taptap.cn/app/{app_id}/review?os=android"
    
    result: Dict[str, Any] = {
        "basic_info": {},
        "official_posts": [],
        "hot_reviews": [],
    }
    
    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            )
            
            page = context.new_page()
            page.set_default_timeout(30000)
            
            # 1. 抓取基础数据页
            logging.info("正在抓取基础数据页: %s", base_url)
            page.goto(base_url, wait_until='networkidle')
            time.sleep(1)  # 等待动态内容加载
            basic_info = extract_basic_info(page)
            result["basic_info"] = basic_info
            logging.info("基础数据: %s", basic_info.get('name', ''))
            
            # 2. 抓取官方帖子页
            logging.info("正在抓取官方帖子页: %s", posts_url)
            page.goto(posts_url, wait_until='networkidle')
            time.sleep(1)
            official_posts = extract_official_posts(page)
            result["official_posts"] = official_posts
            logging.info("获取到 %d 条官方帖子", len(official_posts))
            
            # 3. 抓取热门评论页
            logging.info("正在抓取热门评论页: %s", reviews_url)
            page.goto(reviews_url, wait_until='networkidle')
            time.sleep(2)  # 等待评论列表完全渲染
            fetch_time = datetime.now()  # 记录爬取时间
            hot_reviews = extract_hot_reviews(page, fetch_time)
            result["hot_reviews"] = hot_reviews
            logging.info("获取到 %d 条热门评论", len(hot_reviews))
            
            browser.close()
            
    except PlaywrightTimeout as e:
        logging.error("页面加载超时: %s", e)
    except Exception as e:
        logging.exception("TapTap 抓取失败: %s", e)
    
    return result


# 用于独立测试
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    test_urls = [
        "https://www.taptap.cn/app/786394?os=android",  # 代号：恋人
        "https://www.taptap.cn/app/746164?os=android",  # 夜幕之下
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"测试 URL: {url}")
        print('='*60)
        result = fetch_taptap_data(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
