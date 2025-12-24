#!/bin/bash

# 竞品监控系统 - 手动抓取脚本
# 双击运行即可立即更新数据

# 项目路径
PROJECT_DIR="/Users/turbotang/Documents/工作/如临/竞品监控系统/echo_cms"
LOG_FILE="$PROJECT_DIR/logs/manual_crawl_$(date +%Y%m%d_%H%M%S).log"
GITHUB_ACTIONS_URL="https://github.com/turbotang2333/echo_cms/actions"
WEBSITE_URL="https://turbotang2333.github.io/echo_cms/"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
echo "=========================================="
echo -e "${BLUE}  竞品监控系统 - 手动数据更新${NC}"
echo "=========================================="
echo ""
echo "📅 执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📂 项目路径: $PROJECT_DIR"
echo ""

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 步骤1：运行爬虫
echo "=========================================="
echo -e "${YELLOW}步骤 1/4：运行爬虫抓取数据${NC}"
echo "=========================================="
echo ""
echo "正在抓取数据，请稍候..."
echo "（日志保存到: logs/manual_crawl_*.log）"
echo ""

cd "$PROJECT_DIR"
/usr/bin/python3 "$PROJECT_DIR/crawler/main.py" 2>&1 | tee "$LOG_FILE"

# 检查爬虫是否成功
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 爬虫执行成功${NC}"
else
    echo ""
    echo -e "${RED}❌ 爬虫执行失败，请查看日志${NC}"
    echo "日志文件: $LOG_FILE"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

echo ""

# 步骤2：检查是否有数据变化
echo "=========================================="
echo -e "${YELLOW}步骤 2/4：检查数据变化${NC}"
echo "=========================================="
echo ""

if git diff --quiet public/data.json archive/; then
    echo -e "${YELLOW}⚠️  数据没有变化，无需提交${NC}"
    echo ""
    echo "可能原因："
    echo "  - 平台数据未更新"
    echo "  - 所有游戏配置为 enabled: false"
    echo ""
    read -p "按回车键退出..."
    exit 0
fi

echo -e "${GREEN}✅ 检测到数据已更新${NC}"
echo ""

# 显示变化摘要
echo "变化摘要:"
git diff --stat public/data.json archive/ | head -10
echo ""

# 步骤3：提交并推送
echo "=========================================="
echo -e "${YELLOW}步骤 3/4：提交并推送到 GitHub${NC}"
echo "=========================================="
echo ""

# 暂存其他未提交的修改（避免干扰）
echo "正在暂存工作区..."
git stash -u > /dev/null 2>&1
STASH_CREATED=$?

echo "正在添加数据文件..."
git add public/data.json archive/

echo "正在提交..."
git commit -m "data: 手动数据更新 $(date '+%Y-%m-%d %H:%M')"

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  没有新的提交（数据可能未变化）${NC}"
    if [ $STASH_CREATED -eq 0 ]; then
        git stash pop > /dev/null 2>&1
    fi
    echo ""
    read -p "按回车键退出..."
    exit 0
fi

echo "正在同步远程更新..."
git pull --rebase

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  检测到冲突，正在自动解决...${NC}"
    # 优先使用本地数据文件（因为是刚抓取的最新数据）
    git checkout --ours public/data.json 2>/dev/null
    git checkout --ours archive/ 2>/dev/null
    git add public/data.json archive/
    GIT_EDITOR=true git rebase --continue
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 无法自动解决冲突${NC}"
        echo "请手动执行："
        echo "  cd $PROJECT_DIR"
        echo "  git rebase --abort"
        echo "  git pull --rebase"
        echo ""
        read -p "按回车键退出..."
        exit 1
    fi
    echo -e "${GREEN}✅ 冲突已自动解决${NC}"
fi

echo "正在推送到 GitHub..."
git push

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 推送成功！${NC}"
else
    echo ""
    echo -e "${RED}❌ 推送失败${NC}"
    echo "请检查网络连接或手动执行: git push"
    echo ""
    read -p "按回车键退出..."
    exit 1
fi

# 恢复之前暂存的修改
if [ $STASH_CREATED -eq 0 ]; then
    echo "正在恢复工作区..."
    git stash pop > /dev/null 2>&1
fi

echo ""

# 步骤4：打开部署页面
echo "=========================================="
echo -e "${YELLOW}步骤 4/4：查看部署进度${NC}"
echo "=========================================="
echo ""
echo "正在打开 GitHub Actions 页面..."
sleep 1
open "$GITHUB_ACTIONS_URL"

echo ""
echo "=========================================="
echo -e "${GREEN}  操作完成！${NC}"
echo "=========================================="
echo ""
echo "📋 GitHub Actions 正在构建部署"
echo "📋 部署通常需要 1-2 分钟"
echo "📋 部署完成后访问：$WEBSITE_URL"
echo ""
echo "💡 提示：网站部署完成后，刷新页面即可看到最新数据"
echo ""
read -p "按回车键打开网站并退出..."
open "$WEBSITE_URL"

