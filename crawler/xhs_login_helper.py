# -*- coding: utf-8 -*-
"""
小红书登录助手
用于自动化获取和保存 Cookie
"""
import json
import logging
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright 未安装")


def save_cookies_to_env(cookies_dict: dict) -> None:
    """将 Cookie 保存到 .env 文件"""
    cookie_str = '; '.join([f"{k}={v}" for k, v in cookies_dict.items()])
    
    env_path = Path(__file__).resolve().parent.parent / ".env"
    
    # 读取现有内容
    existing_lines = []
    if env_path.exists():
        with env_path.open("r", encoding="utf-8") as f:
            existing_lines = [line for line in f if not line.startswith("XIAOHONGSHU_COOKIE=")]
    
    # 写入新 Cookie
    with env_path.open("w", encoding="utf-8") as f:
        for line in existing_lines:
            f.write(line)
        f.write(f'XIAOHONGSHU_COOKIE="{cookie_str}"\n')
        f.write(f'# Cookie 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    logging.info("Cookie 已保存到 .env 文件")


def login_and_save_cookies() -> bool:
    """
    启动浏览器，等待用户手动登录，然后保存 Cookie
    
    Returns:
        是否成功获取 Cookie
    """
    if not PLAYWRIGHT_AVAILABLE:
        logging.error("Playwright 未安装，无法使用自动登录功能")
        return False
    
    print("\n" + "="*60)
    print("🔐 小红书登录助手")
    print("="*60)
    print("\n请按以下步骤操作：")
    print("1. 浏览器将自动打开小红书登录页")
    print("2. 请手动完成登录（扫码或验证码）")
    print("3. 登录成功后，会自动保存 Cookie")
    print("4. 完成后可以关闭浏览器\n")
    
    input("按 Enter 键继续...")
    
    try:
        with sync_playwright() as p:
            # 启动浏览器（非无头模式，方便用户操作）
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            )
            
            page = context.new_page()
            
            # 访问小红书首页
            print("\n正在打开小红书...")
            page.goto("https://www.xiaohongshu.com", wait_until='domcontentloaded')
            
            print("\n✅ 浏览器已打开，请在浏览器中完成登录")
            print("⏳ 等待登录中...")
            
            # 等待用户登录（检测是否出现用户头像）
            try:
                # 等待登录成功的标志（如用户头像、个人中心链接等）
                page.wait_for_selector('a[href*="/user/"]', timeout=300000)  # 5分钟超时
                print("\n✅ 检测到登录成功！")
            except Exception:
                print("\n⚠️ 未检测到登录，请确保已完成登录")
                input("如果已登录，请按 Enter 继续...")
            
            # 获取 Cookie
            cookies = context.cookies()
            cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # 检查关键 Cookie
            if 'web_session' not in cookies_dict or 'a1' not in cookies_dict:
                print("\n❌ 未获取到完整的登录 Cookie")
                print("   请确保已成功登录小红书")
                browser.close()
                return False
            
            # 保存 Cookie
            save_cookies_to_env(cookies_dict)
            
            print("\n" + "="*60)
            print("🎉 Cookie 获取成功！")
            print("="*60)
            print(f"\n✅ web_session: {cookies_dict['web_session'][:20]}...")
            print(f"✅ a1: {cookies_dict['a1'][:20]}...")
            print(f"✅ 共 {len(cookies_dict)} 个 Cookie")
            print("\n💾 Cookie 已保存到 .env 文件")
            print("🚀 现在可以运行爬虫了：python3 main.py\n")
            
            input("按 Enter 键关闭浏览器...")
            browser.close()
            
            return True
            
    except Exception as e:
        logging.exception("登录过程出错: %s", e)
        return False


def check_cookie_valid() -> bool:
    """
    检查当前 Cookie 是否有效
    
    Returns:
        Cookie 是否有效
    """
    import os
    import requests
    
    # 读取 Cookie
    env_path = Path(__file__).resolve().parent.parent / ".env"
    cookie_str = ""
    
    if env_path.exists():
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("XIAOHONGSHU_COOKIE="):
                    cookie_str = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    
    if not cookie_str:
        logging.warning("未找到 Cookie 配置")
        return False
    
    # 解析 Cookie
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if '=' in item:
            name, value = item.split('=', 1)
            cookies[name.strip()] = value.strip()
    
    if 'web_session' not in cookies or 'a1' not in cookies:
        logging.warning("Cookie 不完整，缺少关键字段")
        return False
    
    # 测试 Cookie 是否有效（调用一个简单的 API）
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.xiaohongshu.com/',
        }
        
        response = requests.get(
            "https://edith.xiaohongshu.com/api/sns/web/v2/user/me",
            headers=headers,
            cookies=cookies,
            timeout=10
        )
        
        data = response.json()
        
        if data.get("success"):
            logging.info("✅ Cookie 有效")
            return True
        else:
            logging.warning("❌ Cookie 已失效: %s", data.get("msg"))
            return False
            
    except Exception as e:
        logging.error("检查 Cookie 失败: %s", e)
        return False


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # 检查 Cookie 是否有效
        print("\n🔍 检查 Cookie 状态...\n")
        is_valid = check_cookie_valid()
        
        if not is_valid:
            print("\n💡 Cookie 已失效，请运行以下命令重新登录：")
            print("   python3 xhs_login_helper.py\n")
            sys.exit(1)
        else:
            print("\n✅ Cookie 有效，可以正常使用\n")
            sys.exit(0)
    else:
        # 启动登录流程
        success = login_and_save_cookies()
        sys.exit(0 if success else 1)


