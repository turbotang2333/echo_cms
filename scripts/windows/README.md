# Windows 脚本使用指南

## 📋 脚本列表

### 1. `manual_crawl.bat` - 手动数据更新
**用途**: 手动运行爬虫并推送到 GitHub

**使用方法**: 双击运行

**执行步骤**:
1. 运行爬虫抓取数据
2. 检查数据变化
3. Git 提交
4. 推送到 GitHub
5. 打开 GitHub Actions 和网站

---

### 2. `daily_crawl.bat` - 每日定时抓取
**用途**: 由 Windows 任务计划程序调用，实现自动化

**使用方法**: 不需要手动运行，由定时任务自动调用

**功能**:
- 运行爬虫
- 自动提交推送
- 记录日志到 `logs/crawl_YYYYMMDD.log`

---

### 3. `install_scheduled_task.bat` - 安装定时任务
**用途**: 创建 Windows 定时任务，实现每天自动抓取

**使用方法**: 
1. **右键点击** → **以管理员身份运行**
2. 确认创建

**结果**: 每天早上 9:00 自动运行爬虫

---

### 4. `test_scheduled_task.bat` - 测试定时任务
**用途**: 手动测试定时任务脚本是否正常工作

**使用方法**: 双击运行

**功能**: 立即执行一次定时任务（不等到 9:00）

---

## 🚀 快速开始

### 第一步：安装定时任务

1. 找到 `install_scheduled_task.bat`
2. **右键** → **以管理员身份运行**
3. 按 Enter 确认
4. 看到 "SUCCESS!" 表示安装成功

### 第二步：测试定时任务

1. 双击运行 `test_scheduled_task.bat`
2. 等待爬虫完成
3. 检查 `logs/` 目录下的日志文件

### 第三步：验证自动化

- 定时任务会在每天 9:00 自动运行
- 检查日志文件确认执行情况
- 访问 GitHub 查看自动提交

---

## 🔧 系统要求

运行脚本前需要安装：

1. **Python 3** 
   - 下载：https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **Git**
   - 下载：https://git-scm.com/downloads
   - 配置好 GitHub 凭据

3. **Python 依赖**
   ```bash
   py -m pip install -r requirements.txt
   py -m playwright install chromium
   ```

---

## 📝 常用命令

### 查看定时任务
```bash
schtasks /query /tn "EchoCMS_DailyCrawl" /v
```

### 立即运行定时任务
```bash
schtasks /run /tn "EchoCMS_DailyCrawl"
```

### 删除定时任务
```bash
schtasks /delete /tn "EchoCMS_DailyCrawl" /f
```

### 查看日志
```bash
type logs\crawl_20251227.log
```

---

## 🆘 常见问题

### Q: 脚本运行后自动消失？
**A**: 这是 iCloud 同步导致的，不影响使用。脚本已保存在 Git 中，可以随时恢复。

### Q: Python not found?
**A**: 
1. 安装 Python: https://www.python.org/
2. 确保勾选 "Add Python to PATH"
3. 重启命令行窗口

### Q: Git push 失败？
**A**: 
1. 检查网络连接
2. 验证 Git 凭据：`git config --list`
3. 手动推送测试：`git push`

### Q: 定时任务没有运行？
**A**: 
1. 确保电脑在 9:00 时是开机状态
2. 检查任务计划程序中的任务状态
3. 查看日志文件是否有新记录

### Q: 小红书数据抓取失败？
**A**: 这是已知问题（JavaScript 签名兼容性），不影响其他平台。可以暂时忽略。

---

## 📊 日志文件

### 手动抓取日志
- 位置: `logs/manual_crawl_YYYYMMDD_HHMMSS.log`
- 包含: 完整的爬虫输出

### 定时任务日志
- 位置: `logs/crawl_YYYYMMDD.log`
- 包含: 爬虫输出 + Git 操作记录

---

## 💡 提示

1. **首次运行**: 建议先运行 `test_scheduled_task.bat` 测试
2. **检查日志**: 定期查看日志文件确认运行状态
3. **电脑休眠**: 定时任务需要电脑处于开机状态
4. **网络连接**: 确保网络畅通，否则无法推送到 GitHub

---

## 🎯 完整工作流程

```
每天 9:00
    ↓
Windows 任务计划程序触发
    ↓
运行 daily_crawl.bat
    ↓
执行爬虫 (TapTap + B站 + 微博)
    ↓
数据写入 data.json 和 archive/
    ↓
Git commit + push
    ↓
GitHub Actions 自动部署
    ↓
网站更新完成
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看日志文件
2. 检查系统要求是否满足
3. 参考常见问题部分

