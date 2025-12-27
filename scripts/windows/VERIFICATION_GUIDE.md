# 验证指南 - 如何确认数据已更新到生产环境

## 🎯 快速验证

### 方法 1：使用状态检查脚本（推荐）

双击运行：**`check_status.bat`**

这个脚本会自动检查：
1. ✅ 最新的爬虫日志
2. ✅ 本地数据文件更新时间
3. ✅ Git 提交状态
4. ✅ GitHub Actions 部署状态

---

## 📋 完整验证流程

### 第 1 步：检查爬虫是否成功运行

#### 查看日志文件
```bash
# 找到最新的日志文件
dir /o-d logs\crawl_*.log

# 查看日志内容
type logs\crawl_20251227.log
```

#### 成功标志
在日志文件末尾应该看到：
```
Crawler success
Push success
End: 周六 2025/12/27 22:33:35.46
```

---

### 第 2 步：检查本地数据是否更新

#### 查看 data.json
```bash
# 查看文件修改时间
dir public\data.json

# 查看文件内容（前几行）
powershell -Command "Get-Content public\data.json -Head 20"
```

#### 验证要点
- 文件修改时间应该是最近的
- `last_updated` 字段应该是今天的日期时间

---

### 第 3 步：检查 Git 提交

#### 查看最新提交
```bash
# 查看最新的提交记录
git log -1

# 查看提交的文件
git show --stat
```

#### 验证要点
- 提交信息：`data: daily update 2025/12/27` 或 `data: manual update ...`
- 提交文件：应该包含 `public/data.json` 和 `archive/2025-12.json`

#### 检查是否已推送
```bash
# 检查本地和远程的差异
git status
```

应该显示：`Your branch is up to date with 'origin/main'`

---

### 第 4 步：检查 GitHub Actions 部署

#### 方法 A：访问 GitHub Actions 页面
打开：https://github.com/turbotang2333/echo_cms/actions

查看：
- ✅ 最新的 workflow 应该是绿色（成功）
- ✅ 运行时间应该是最近的
- ✅ 状态应该是 "Success"

#### 方法 B：使用命令行
```bash
# 使用 PowerShell 查询
powershell -Command "Invoke-RestMethod -Uri 'https://api.github.com/repos/turbotang2333/echo_cms/actions/runs?per_page=1' | Select-Object -ExpandProperty workflow_runs | Select-Object status, conclusion, created_at"
```

---

### 第 5 步：验证生产网站

#### 访问网站
打开：https://turbotang2333.github.io/echo_cms/

#### 验证要点

1. **检查数据时间戳**
   - 打开浏览器开发者工具（F12）
   - 切换到 Console 标签
   - 输入：`fetch('/echo_cms/data.json').then(r=>r.json()).then(d=>console.log(d[0].last_updated))`
   - 查看输出的时间是否是最新的

2. **强制刷新页面**
   - Windows: `Ctrl + F5`
   - 确保看到最新数据，不是缓存

3. **检查游戏数据**
   - 查看各个游戏的粉丝数、动态等
   - 对比本地 `public/data.json` 的数据

---

## ⏱️ 时间线参考

从爬虫运行到网站更新的完整时间线：

```
09:00:00  定时任务触发
09:00:05  爬虫开始运行
09:01:30  爬虫完成（约1-2分钟）
09:01:35  Git commit
09:01:40  Git push 完成
09:01:45  GitHub Actions 触发
09:02:30  构建完成
09:03:00  部署到 GitHub Pages
09:03:30  网站更新完成（CDN 缓存刷新）
```

**总耗时**：约 3-5 分钟

---

## 🔍 常见问题排查

### Q1: 爬虫运行了，但 Git 没有新提交？

**可能原因**：
- 数据没有变化（平台数据未更新）
- 所有游戏都配置为 `enabled: false`

**检查方法**：
```bash
git diff public/data.json
```

---

### Q2: Git 提交了，但 GitHub 上看不到？

**可能原因**：
- Push 失败（网络问题）
- Git 凭据过期

**检查方法**：
```bash
# 查看日志中的 push 结果
type logs\crawl_20251227.log | findstr "Push"

# 手动推送测试
git push
```

---

### Q3: GitHub Actions 运行了，但网站没更新？

**可能原因**：
- 浏览器缓存
- CDN 缓存未刷新

**解决方法**：
1. 强制刷新：`Ctrl + F5`
2. 清除浏览器缓存
3. 等待 5-10 分钟（CDN 缓存刷新）
4. 使用隐私/无痕模式打开

---

### Q4: 如何确认 CDN 缓存是否刷新？

**方法 1：检查 data.json 文件**
```bash
# 使用 curl 或 PowerShell 获取线上文件
powershell -Command "Invoke-RestMethod -Uri 'https://turbotang2333.github.io/echo_cms/data.json' | Select-Object -First 1 | Select-Object last_updated"
```

**方法 2：添加时间戳参数**
```
https://turbotang2333.github.io/echo_cms/?t=1234567890
```

---

## 📊 监控建议

### 每日检查清单

- [ ] 查看 `logs/crawl_YYYYMMDD.log` 确认爬虫成功
- [ ] 访问 GitHub Actions 确认部署成功
- [ ] 访问网站确认数据已更新
- [ ] 检查是否有错误日志

### 每周检查清单

- [ ] 检查归档文件 `archive/YYYY-MM.json`
- [ ] 验证所有平台数据正常
- [ ] 检查磁盘空间（日志文件）

---

## 🛠️ 快速命令参考

```bash
# 查看最新日志
type logs\crawl_20251227.log

# 查看 Git 状态
git status

# 查看最新提交
git log -1

# 手动触发定时任务
schtasks /run /tn "EchoCMS_DailyCrawl"

# 查看定时任务状态
schtasks /query /tn "EchoCMS_DailyCrawl"

# 打开网站
start https://turbotang2333.github.io/echo_cms/

# 打开 GitHub Actions
start https://github.com/turbotang2333/echo_cms/actions
```

---

## 📱 移动端验证

如果需要在手机上验证：

1. 访问：https://turbotang2333.github.io/echo_cms/
2. 下拉刷新页面
3. 检查数据时间戳
4. 对比电脑上的数据

---

## 🎯 自动化监控（进阶）

如果需要自动监控，可以：

1. **添加邮件通知**
   - 修改 `daily_crawl.bat`
   - 失败时发送邮件

2. **添加健康检查**
   - 创建定时检查脚本
   - 验证网站可访问性

3. **集成监控服务**
   - UptimeRobot
   - Pingdom
   - StatusCake

---

## 💡 最佳实践

1. **每天早上 9:30 检查一次**
   - 给系统 30 分钟完成整个流程
   - 查看日志确认无误

2. **遇到问题时**
   - 先查看日志文件
   - 再检查 GitHub Actions
   - 最后检查网站

3. **定期清理**
   - 每月清理旧日志文件
   - 保留最近 30 天即可

---

## 📞 需要帮助？

如果验证过程中遇到问题：

1. 运行 `check_status.bat` 获取完整状态
2. 查看日志文件中的错误信息
3. 检查网络连接
4. 验证 Git 凭据

