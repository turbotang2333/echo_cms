#!/bin/bash

# 竞品监控系统 - 卸载 launchd 定时任务

PLIST_TARGET="$HOME/Library/LaunchAgents/com.echo_cms.daily_crawl.plist"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

clear
echo "=========================================="
echo -e "${YELLOW}  竞品监控系统 - 卸载定时任务${NC}"
echo "=========================================="
echo ""

if [ ! -f "$PLIST_TARGET" ]; then
    echo -e "${YELLOW}⚠️  未找到定时任务配置文件${NC}"
    echo ""
    read -p "按回车键退出..."
    exit 0
fi

echo "即将卸载定时任务："
echo "  文件：$PLIST_TARGET"
echo ""
read -p "确认卸载？(y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "取消卸载"
    exit 0
fi

echo ""
echo "正在卸载..."

# 卸载任务
launchctl unload "$PLIST_TARGET" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 任务已停止${NC}"
else
    echo -e "${YELLOW}⚠️  任务可能未运行${NC}"
fi

# 删除配置文件
rm "$PLIST_TARGET"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 配置文件已删除${NC}"
else
    echo -e "${RED}❌ 删除失败${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  卸载完成！${NC}"
echo "=========================================="
echo ""
read -p "按回车键退出..."



