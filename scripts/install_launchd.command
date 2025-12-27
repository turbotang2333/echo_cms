#!/bin/bash

# 竞品监控系统 - 安装 launchd 定时任务
# 用途：替代 crontab，解决权限问题

# 项目路径
PROJECT_DIR="/Users/turbotang/Documents/工作/如临/竞品监控系统/echo_cms"
PLIST_SOURCE="$PROJECT_DIR/scripts/com.echo_cms.daily_crawl.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/com.echo_cms.daily_crawl.plist"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
echo "=========================================="
echo -e "${BLUE}  竞品监控系统 - 定时任务安装${NC}"
echo "=========================================="
echo ""

# 步骤1：检查旧的 crontab
echo -e "${YELLOW}步骤 1/5：检查现有定时任务${NC}"
echo ""

if crontab -l 2>/dev/null | grep -q "daily_crawl.sh"; then
    echo "⚠️  检测到 crontab 定时任务"
    echo ""
    echo "当前 crontab 配置："
    crontab -l | grep "daily_crawl.sh"
    echo ""
    read -p "是否删除旧的 crontab 任务？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        crontab -l | grep -v "daily_crawl.sh" | crontab -
        echo -e "${GREEN}✅ 已删除旧的 crontab 任务${NC}"
    else
        echo -e "${YELLOW}⚠️  保留 crontab 任务（可能会重复执行）${NC}"
    fi
else
    echo "✅ 未检测到 crontab 任务"
fi

echo ""

# 步骤2：创建 LaunchAgents 目录
echo -e "${YELLOW}步骤 2/5：准备 LaunchAgents 目录${NC}"
echo ""

mkdir -p "$HOME/Library/LaunchAgents"
echo "✅ LaunchAgents 目录已就绪"
echo ""

# 步骤3：复制 plist 文件
echo -e "${YELLOW}步骤 3/5：安装配置文件${NC}"
echo ""

if [ -f "$PLIST_TARGET" ]; then
    echo "⚠️  检测到已存在的配置文件"
    read -p "是否覆盖？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消安装"
        exit 0
    fi
    # 卸载旧任务
    launchctl unload "$PLIST_TARGET" 2>/dev/null
fi

cp "$PLIST_SOURCE" "$PLIST_TARGET"
echo "✅ 配置文件已复制到: $PLIST_TARGET"
echo ""

# 步骤4：加载任务
echo -e "${YELLOW}步骤 4/5：加载定时任务${NC}"
echo ""

launchctl load "$PLIST_TARGET"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 定时任务加载成功${NC}"
else
    echo -e "${RED}❌ 加载失败，请检查配置文件${NC}"
    exit 1
fi

echo ""

# 步骤5：验证任务
echo -e "${YELLOW}步骤 5/5：验证任务状态${NC}"
echo ""

if launchctl list | grep -q "com.echo_cms.daily_crawl"; then
    echo -e "${GREEN}✅ 任务已成功注册${NC}"
    echo ""
    echo "任务详情："
    launchctl list | grep "com.echo_cms.daily_crawl"
else
    echo -e "${RED}❌ 任务未找到${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  安装完成！${NC}"
echo "=========================================="
echo ""
echo "📋 定时任务信息："
echo "   - 执行时间：每天 9:00"
echo "   - 执行脚本：daily_crawl.sh"
echo "   - 标准输出：logs/launchd_out.log"
echo "   - 错误输出：logs/launchd_err.log"
echo ""
echo "💡 常用命令："
echo "   - 查看任务状态：launchctl list | grep echo_cms"
echo "   - 立即执行测试：launchctl start com.echo_cms.daily_crawl"
echo "   - 卸载任务：launchctl unload ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist"
echo "   - 重新加载：launchctl load ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist"
echo ""
read -p "是否立即测试运行？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "正在执行测试..."
    launchctl start com.echo_cms.daily_crawl
    echo ""
    echo "测试已启动，请稍候..."
    sleep 5
    echo ""
    echo "查看最新日志："
    tail -20 "$PROJECT_DIR/logs/launchd_err.log"
    echo ""
fi

echo "按回车键退出..."
read



