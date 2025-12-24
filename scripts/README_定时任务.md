# 定时任务配置说明

## 📋 问题说明

**原问题：** crontab 定时任务遇到 `Operation not permitted` 权限错误

**原因：** Mac 的 crontab 默认没有完全磁盘访问权限，无法执行项目脚本

**解决方案：** 使用 `launchd`（Mac 官方推荐的定时任务方案）

---

## 🚀 快速安装

### 方式 1：桌面双击（推荐）

双击桌面上的 **`安装定时任务.command`**

### 方式 2：命令行安装

```bash
cd /Users/turbotang/Documents/工作/如临/竞品监控系统/echo_cms/scripts
./install_launchd.command
```

---

## 📝 安装步骤

安装脚本会自动完成以下操作：

1. ✅ 检查并删除旧的 crontab 任务
2. ✅ 创建 `~/Library/LaunchAgents` 目录
3. ✅ 复制配置文件到系统目录
4. ✅ 加载定时任务
5. ✅ 验证任务状态

---

## ⚙️ 配置详情

### 任务标识
```
com.echo_cms.daily_crawl
```

### 执行时间
```
每天 9:00
```

### 执行脚本
```
/Users/turbotang/Documents/工作/如临/竞品监控系统/echo_cms/scripts/daily_crawl.sh
```

### 日志文件
- **标准输出：** `logs/launchd_out.log`
- **错误输出：** `logs/launchd_err.log`

---

## 🛠️ 常用命令

### 查看任务状态
```bash
launchctl list | grep echo_cms
```

### 立即执行测试
```bash
launchctl start com.echo_cms.daily_crawl
```

### 停止任务
```bash
launchctl stop com.echo_cms.daily_crawl
```

### 卸载任务
```bash
# 方式 1：使用卸载脚本
./uninstall_launchd.command

# 方式 2：手动卸载
launchctl unload ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist
rm ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist
```

### 重新加载任务
```bash
launchctl unload ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist
launchctl load ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist
```

### 查看日志
```bash
# 查看错误日志
tail -f logs/launchd_err.log

# 查看标准输出
tail -f logs/launchd_out.log

# 查看爬虫日志
tail -f logs/crawl_$(date +%Y%m%d).log
```

---

## 🆚 launchd vs crontab

| 特性 | launchd | crontab |
|------|---------|---------|
| **权限问题** | ✅ 无权限问题 | ❌ 需要手动授权 |
| **Mac 休眠** | ✅ 休眠后自动补执行 | ❌ 休眠时不执行 |
| **日志管理** | ✅ 自动记录 | ⚪ 需手动配置 |
| **官方推荐** | ✅ Mac 官方方案 | ⚪ Unix 传统方案 |
| **配置复杂度** | ⚪ 需要 plist 文件 | ✅ 简单易懂 |

---

## ⚠️ 注意事项

### 1. Mac 需保持开机
虽然 launchd 比 crontab 更可靠，但 Mac 关机时仍无法执行。

**建议：**
- 设置 Mac 定时唤醒（系统偏好设置 → 节能）
- 或使用云服务器（GitHub Actions）

### 2. 首次安装可能需要授权
Mac 可能提示"无法验证开发者"：
- 右键点击 → "打开" → 确认运行

### 3. 修改配置后需重新加载
如果修改了 `com.echo_cms.daily_crawl.plist`，需要：
```bash
launchctl unload ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist
launchctl load ~/Library/LaunchAgents/com.echo_cms.daily_crawl.plist
```

---

## 🐛 故障排查

### 问题 1：任务未执行

**检查步骤：**
```bash
# 1. 确认任务已加载
launchctl list | grep echo_cms

# 2. 查看错误日志
tail -50 logs/launchd_err.log

# 3. 手动测试脚本
./scripts/daily_crawl.sh
```

### 问题 2：权限错误

**解决方案：**
```bash
# 确保脚本有执行权限
chmod +x scripts/daily_crawl.sh
chmod +x scripts/install_launchd.command
```

### 问题 3：任务重复执行

**原因：** crontab 和 launchd 同时运行

**解决方案：**
```bash
# 删除 crontab 任务
crontab -l | grep -v "daily_crawl.sh" | crontab -
```

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `com.echo_cms.daily_crawl.plist` | launchd 配置文件 |
| `install_launchd.command` | 安装脚本 |
| `uninstall_launchd.command` | 卸载脚本 |
| `daily_crawl.sh` | 实际执行的爬虫脚本 |

---

## 🎯 验证安装成功

安装完成后，执行以下命令验证：

```bash
# 1. 检查任务是否加载
launchctl list | grep echo_cms
# 应该看到：com.echo_cms.daily_crawl

# 2. 立即测试运行
launchctl start com.echo_cms.daily_crawl

# 3. 等待 30 秒后查看日志
tail -50 logs/launchd_err.log

# 4. 如果看到爬虫日志，说明成功！
```

---

## 💡 推荐工作流

### 日常使用
- ✅ 让 launchd 每天 9:00 自动运行
- ✅ 需要立即更新时，双击"手动更新竞品数据.command"

### 调试阶段
- ✅ 使用 `launchctl start` 手动触发测试
- ✅ 实时查看日志：`tail -f logs/launchd_err.log`

### 长期维护
- ✅ 定期检查日志文件大小
- ✅ 每月清理旧日志：`rm logs/crawl_202*.log`

---

**安装完成后，定时任务将在每天 9:00 自动运行，无需人工干预！** ✅

