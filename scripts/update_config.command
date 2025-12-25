#!/bin/bash

# 竞品监控系统 - 配置更新脚本
# 双击运行即可编辑并推送配置

# 项目路径
PROJECT_DIR="/Users/turbotang/Documents/工作/如临/竞品监控系统/echo_cms"
CONFIG_FILE="$PROJECT_DIR/public/games_config.json"
GITHUB_ACTIONS_URL="https://github.com/turbotang2333/echo_cms/actions"
WEBSITE_URL="https://turbotang2333.github.io/echo_cms/"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear
echo "=========================================="
echo -e "${BLUE}  竞品监控系统 - 配置更新工具${NC}"
echo "=========================================="
echo ""

# 步骤1：打开配置文件
echo -e "${YELLOW}步骤 1/4：打开配置文件${NC}"
echo "正在用 TextEdit 打开 games_config.json..."
echo ""
open -a TextEdit "$CONFIG_FILE"

# 等待用户编辑
echo "=========================================="
echo -e "${GREEN}请在 TextEdit 中编辑配置文件${NC}"
echo "编辑完成后，保存文件 (Cmd+S)，然后关闭 TextEdit"
echo "=========================================="
echo ""
read -p "编辑完成后，按回车键继续..."
echo ""

# 步骤2：检查是否有修改
echo -e "${YELLOW}步骤 2/4：检查修改${NC}"
cd "$PROJECT_DIR"
if git diff --quiet public/games_config.json; then
    echo "⚠️  配置文件没有修改，无需提交"
    echo ""
    read -p "按回车键退出..."
    exit 0
fi

echo "✅ 检测到配置文件已修改"
echo ""

# 步骤3：提交并推送
echo -e "${YELLOW}步骤 3/4：提交并推送到 GitHub${NC}"
echo ""
echo "正在添加文件..."
git add public/games_config.json

echo "正在提交..."
git commit -m "config: 更新游戏配置 $(date '+%Y-%m-%d %H:%M')"

echo "正在推送..."
git push

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 推送成功！${NC}"
else
    echo ""
    echo "❌ 推送失败，请检查网络连接"
    read -p "按回车键退出..."
    exit 1
fi

echo ""

# 步骤4：打开部署页面
echo -e "${YELLOW}步骤 4/4：查看部署进度${NC}"
echo ""
echo "正在打开 GitHub Actions 页面..."
open "$GITHUB_ACTIONS_URL"

echo ""
echo "=========================================="
echo -e "${GREEN}  操作完成！${NC}"
echo "=========================================="
echo ""
echo "📋 部署通常需要 1-2 分钟"
echo "📋 部署完成后访问：$WEBSITE_URL"
echo ""
read -p "按回车键打开网站并退出..."
open "$WEBSITE_URL"








