# -*- coding: utf-8 -*-
"""
小红书数据抓取模块
使用 Playwright 浏览器自动化提取数据
需要 Cookie 登录态
"""
from __future__ import annotations

import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 尝试导入 Playwright
try:
    from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright 未安装，小红书抓取功能不可用。请运行: pip install playwright && playwright install chromium")


def load_cookie_from_env() -> str:
    """从环境变量或 .env 文件加载 Cookie"""
    # 尝试从环境变量读取
    cookie = os.getenv("XIAOHONGSHU_COOKIE", "")
    
    # 如果环境变量没有，尝试从 .env 文件读取
    if not cookie:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            with env_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("XIAOHONGSHU_COOKIE="):
                        cookie = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    
    if not cookie or cookie == "your_cookie_here":
        logging.warning("小红书 Cookie 未配置，可能无法获取完整数据。请在 .env 文件中配置 XIAOHONGSHU_COOKIE")
        return ""
    
    return cookie


def convert_relative_time(relative_time: str, fetch_time: datetime = None) -> str:
    """
    把相对时间转换为绝对日期
    
    Args:
        relative_time: 如 "2天前"、"19小时前"、"2024-12-20"
        fetch_time: 爬取时间，默认为当前时间
        
    Returns:
        格式化的日期字符串，如 "12/23"
    """
    if not relative_time:
        return ""
    
    fetch_time = fetch_time or datetime.now()
    
    # 已经是绝对日期格式 YYYY-MM-DD
    match = re.match(r'(\d{4})-(\d+)-(\d+)', relative_time)
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


def random_sleep(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """随机延迟，模拟人类操作"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def extract_user_id(url: str) -> Optional[str]:
    """从小红书 URL 提取 user_id"""
    match = re.search(r'/user/profile/([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None


def parse_count(count_str: str) -> Optional[int]:
    """
    解析数量字符串，返回整数
    
    Args:
        count_str: 如 "10.1万", "1234", "0"
        
    Returns:
        整数值，失败返回 None
    """
    if not count_str or count_str == "-":
        return None
    
    try:
        # 去除空格
        count_str = count_str.strip()
        
        # 处理 "万" 单位
        if "万" in count_str:
            num_str = count_str.replace("万", "").strip()
            return int(float(num_str) * 10000)
        
        # 直接转整数
        return int(count_str)
    except Exception:
        return None


def extract_basic_info(page: Page) -> Dict[str, Any]:
    """从用户主页提取基础信息"""
    js_code = """
    () => {
        const data = {};
        
        // 获取页面所有文本
        const text = document.body.innerText;
        
        // 提取粉丝数、关注数、获赞与收藏
        // 格式：关注 XXX 粉丝 XXX 获赞与收藏 XXX
        const followingMatch = text.match(/关注[\\s\\n]+(\\d+(?:\\.\\d+)?万?)/);
        const followersMatch = text.match(/粉丝[\\s\\n]+(\\d+(?:\\.\\d+)?万?\\+?)/);
        const likesMatch = text.match(/获赞与收藏[\\s\\n]+(\\d+(?:\\.\\d+)?万?\\+?)/);
        
        data.xhs_following = followingMatch ? followingMatch[1] : '0';
        data.xhs_followers = followersMatch ? followersMatch[1] : '0';
        data.xhs_likes = likesMatch ? likesMatch[1] : '0';
        
        // 获取用户名
        const nameEl = document.querySelector('.user-name');
        data.user_name = nameEl ? nameEl.textContent.trim() : '';
        
        return data;
    }
    """
    try:
        result = page.evaluate(js_code)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        logging.error("提取小红书基础数据失败: %s", e)
        return {}


def extract_posts(page: Page, fetch_time: datetime = None) -> List[Dict[str, Any]]:
    """
    从用户主页提取最新的 5 条非置顶笔记
    
    Args:
        page: Playwright Page 对象
        fetch_time: 爬取时间
        
    Returns:
        笔记列表
    """
    fetch_time = fetch_time or datetime.now()
    
    js_code = """
    () => {
        const posts = [];
        const seenUrls = new Set();
        
        // 查找所有笔记链接（多种可能的选择器）
        const selectors = [
            'a[href*="/explore/"]',
            'a[href*="/discovery/item/"]',
            '.note-item a',
            '.feeds-page a'
        ];
        
        let noteLinks = [];
        for (const selector of selectors) {
            const links = document.querySelectorAll(selector);
            if (links.length > 0) {
                noteLinks = links;
                break;
            }
        }
        
        console.log('找到笔记链接数量:', noteLinks.length);
        
        for (const link of noteLinks) {
            const href = link.getAttribute('href');
            if (!href || seenUrls.has(href)) continue;
            
            // 只处理笔记链接
            if (!href.includes('/explore/') && !href.includes('/discovery/item/')) continue;
            
            seenUrls.add(href);
            
            // 向上查找笔记卡片容器（扩大搜索范围）
            let card = link;
            for (let i = 0; i < 8; i++) {
                card = card.parentElement;
                if (!card) break;
            }
            
            if (!card) continue;
            
            const cardText = card.innerText || '';
            
            // 检查是否为置顶
            if (cardText.includes('置顶')) {
                console.log('跳过置顶内容');
                continue;
            }
            
            // 提取标题（尝试多种方式）
            let title = '';
            
            // 方式1：从链接文本提取
            const linkText = link.textContent.trim();
            if (linkText && linkText.length >= 5 && linkText.length <= 100) {
                title = linkText;
            }
            
            // 方式2：从卡片中查找标题元素
            if (!title) {
                const titleEl = card.querySelector('.title, .note-title, [class*="title"]');
                if (titleEl) {
                    title = titleEl.textContent.trim();
                }
            }
            
            // 方式3：从图片 alt 属性提取
            if (!title) {
                const img = link.querySelector('img');
                if (img && img.alt && img.alt.length >= 5) {
                    title = img.alt;
                }
            }
            
            if (!title || title.length < 3) {
                console.log('标题为空，跳过');
                continue;
            }
            
            // 提取点赞数和评论数
            const likes = '0';  // 主页不显示点赞数
            const comments = '0';  // 主页不显示评论数
            
            // 构建完整 URL
            const url = href.startsWith('http') ? href : 'https://www.xiaohongshu.com' + href;
            
            // 提取笔记 ID
            const idMatch = href.match(/\\/(?:explore|discovery\\/item)\\/([a-zA-Z0-9]+)/);
            const id = idMatch ? idMatch[1] : '';
            
            posts.push({
                id: id,
                title: title.substring(0, 50),
                url: url,
                likes: likes,
                comments: comments,
                rawDate: ''
            });
            
            console.log('提取笔记:', title.substring(0, 30));
            
            if (posts.length >= 10) break;
        }
        
        console.log('最终提取笔记数量:', posts.length);
        return posts;
    }
    """
    
    try:
        result = page.evaluate(js_code)
        if not isinstance(result, list):
            return []
        
        # 处理日期（小红书主页不显示时间，统一使用今天）
        # 如果需要精确时间，需要进入每个笔记详情页抓取（性能开销大）
        today_str = f"{fetch_time.month}/{fetch_time.day}"
        
        for post in result:
            raw_date = post.pop('rawDate', '')
            if raw_date:
                post['date'] = convert_relative_time(raw_date, fetch_time)
            else:
                # 无时间信息，默认标记为今天
                post['date'] = today_str
            
            # is_new 判断（本周发布）
            # 由于没有精确时间，暂时标记为 False，后续可以优化
            post['is_new'] = False
        
        # 返回前 5 条
        return result[:5]
        
    except Exception as e:
        logging.error("提取小红书笔记失败: %s", e)
        return []


def fetch_xiaohongshu_data(url: str) -> Dict[str, Any]:
    """
    抓取小红书用户数据
    
    Args:
        url: 小红书用户主页 URL，如 https://www.xiaohongshu.com/user/profile/xxx
        
    Returns:
        包含 basic_info, official_posts 的字典
    """
    if not PLAYWRIGHT_AVAILABLE:
        logging.error("Playwright 未安装，无法抓取小红书数据")
        return {}
    
    user_id = extract_user_id(url)
    if not user_id:
        logging.error("无法从 URL 提取 user_id: %s", url)
        return {}
    
    # 加载 Cookie
    cookie_str = load_cookie_from_env()
    
    result: Dict[str, Any] = {
        "basic_info": {},
        "official_posts": [],
    }
    
    try:
        with sync_playwright() as p:
            # 启动浏览器（增强反检测）
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                extra_http_headers={
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.xiaohongshu.com/',
                }
            )
            
            # 注入反检测脚本
            context.add_init_script("""
                // 隐藏 webdriver 特征
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 伪装 Chrome 插件
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // 伪装语言
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)
            
            # 注入 Cookie（必须先访问域名才能设置 Cookie）
            if cookie_str:
                # 先访问首页，建立域名上下文
                page_temp = context.new_page()
                page_temp.goto("https://www.xiaohongshu.com", wait_until='domcontentloaded', timeout=15000)
                page_temp.close()
                
                # 解析并注入 Cookie
                cookies = []
                for item in cookie_str.split(';'):
                    item = item.strip()
                    if '=' in item:
                        name, value = item.split('=', 1)
                        cookies.append({
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': '.xiaohongshu.com',
                            'path': '/',
                        })
                
                if cookies:
                    context.add_cookies(cookies)
                    logging.info("已注入 %d 个 Cookie", len(cookies))
                else:
                    logging.warning("Cookie 解析失败，可能无法获取完整数据")
            
            page = context.new_page()
            page.set_default_timeout(60000)  # 增加到 60 秒
            
            # 访问用户主页
            logging.info("正在访问小红书用户主页: %s", url)
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
                # 等待关键元素加载
                page.wait_for_selector('body', timeout=10000)
            except Exception as e:
                logging.warning("页面加载警告: %s，尝试继续提取数据", e)
                # 即使超时也尝试提取数据
            
            # 随机延迟，等待动态内容加载
            random_sleep(2, 4)
            
            # 提取基础数据
            basic_info = extract_basic_info(page)
            result["basic_info"] = basic_info
            logging.info("小红书基础数据: 粉丝 %s, 获赞 %s", 
                        basic_info.get('xhs_followers', '0'),
                        basic_info.get('xhs_likes', '0'))
            
            # 滚动页面，加载更多笔记
            try:
                for i in range(3):
                    page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/4})")
                    random_sleep(0.5, 1)
            except Exception as e:
                logging.warning("滚动页面失败: %s", e)
            
            # 提取笔记列表
            fetch_time = datetime.now()
            
            # 保存页面 HTML 用于调试
            try:
                html_content = page.content()
                debug_path = Path(__file__).resolve().parent.parent / "xhs_debug.html"
                with debug_path.open("w", encoding="utf-8") as f:
                    f.write(html_content)
                logging.info("页面 HTML 已保存到: %s", debug_path)
            except Exception as e:
                logging.warning("保存调试 HTML 失败: %s", e)
            
            posts = extract_posts(page, fetch_time)
            result["official_posts"] = posts
            logging.info("获取到 %d 条小红书笔记", len(posts))
            
            # 如果没有笔记，输出页面调试信息
            if not posts:
                page_text = page.evaluate("() => document.body.innerText")
                logging.warning("未找到笔记！页面文本前800字符: %s", page_text[:800] if page_text else "无内容")
                
                # 输出所有链接用于调试
                all_links = page.evaluate("""
                    () => {
                        const links = [];
                        document.querySelectorAll('a').forEach(a => {
                            const href = a.getAttribute('href');
                            if (href) links.push(href);
                        });
                        return links.slice(0, 20);
                    }
                """)
                logging.warning("页面前20个链接: %s", all_links)
            
            browser.close()
            
    except PlaywrightTimeout as e:
        logging.error("小红书页面加载超时: %s", e)
        logging.info("提示：如果持续超时，可能是网络问题或小红书反爬限制")
    except Exception as e:
        logging.exception("小红书抓取失败: %s", e)
    
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
