#!/bin/bash

# 竞品监控系统 - 每日爬虫脚本
# 功能：运行爬虫 -> Git提交 -> 推送到远程

# 项目路径
PROJECT_DIR="/Users/turbotang/Documents/工作/如临/竞品监控系统/echo_cms"
LOG_FILE="$PROJECT_DIR/logs/crawl_$(date +%Y%m%d).log"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "开始执行: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# 进入项目目录
cd "$PROJECT_DIR"

# 运行爬虫
echo "运行爬虫..." >> "$LOG_FILE"
/usr/bin/python3 "$PROJECT_DIR/crawler/main.py" >> "$LOG_FILE" 2>&1

# 检查爬虫是否成功
if [ $? -eq 0 ]; then
    echo "爬虫执行成功" >> "$LOG_FILE"
    
    # Git 提交
    echo "Git 提交..." >> "$LOG_FILE"
    cd "$PROJECT_DIR"
    git add public/data.json archive/ >> "$LOG_FILE" 2>&1
    git commit -m "data: 每日数据更新 $(date '+%Y-%m-%d')" >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        echo "没有新的提交" >> "$LOG_FILE"
    else
        # 同步远程更新
        echo "同步远程更新..." >> "$LOG_FILE"
        git pull --rebase >> "$LOG_FILE" 2>&1
        
        if [ $? -ne 0 ]; then
            echo "检测到冲突，自动解决..." >> "$LOG_FILE"
            git checkout --ours public/data.json >> "$LOG_FILE" 2>&1
            git checkout --ours archive/ >> "$LOG_FILE" 2>&1
            git add public/data.json archive/ >> "$LOG_FILE" 2>&1
            GIT_EDITOR=true git rebase --continue >> "$LOG_FILE" 2>&1
        fi
        
        # Git 推送
        echo "Git 推送..." >> "$LOG_FILE"
        git push >> "$LOG_FILE" 2>&1
        
        if [ $? -eq 0 ]; then
            echo "推送成功" >> "$LOG_FILE"
        else
            echo "推送失败" >> "$LOG_FILE"
        fi
    fi
else
    echo "爬虫执行失败" >> "$LOG_FILE"
fi

echo "执行完成: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"








