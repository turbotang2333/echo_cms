# Cookie 自动化获取指南

## 🎯 问题

小红书 Cookie 有效期短（几小时到几天），需要频繁手动更新。

## ✅ 解决方案

使用 **登录助手** 半自动化获取 Cookie。

---

## 🚀 使用方法

### 首次配置 / Cookie 过期时

运行登录助手：

```bash
cd crawler
python3 xhs_login_helper.py
```

**操作流程：**

1. 脚本会自动打开浏览器（Chrome）
2. 在浏览器中**手动完成登录**（扫码或验证码）
3. 登录成功后，脚本自动提取并保存 Cookie
4. Cookie 自动写入 `.env` 文件

**优点：**
- ✅ 无需手动复制 Cookie
- ✅ 自动提取完整的 Cookie（包括 HttpOnly 的 `web_session`）
- ✅ 自动保存到配置文件

---

## 🔍 检查 Cookie 状态

随时检查 Cookie 是否有效：

```bash
cd crawler
python3 xhs_login_helper.py check
```

**输出示例：**

```
✅ Cookie 有效，可以正常使用
```

或

```
❌ Cookie 已失效
💡 请运行以下命令重新登录：
   python3 xhs_login_helper.py
```

---

## 🤖 自动检测（已集成）

主爬虫 `main.py` 已集成自动检测：

```bash
python3 main.py
```

如果 Cookie 失效，会自动提示：

```
⚠️ 小红书 Cookie 已失效，小红书数据将无法抓取
💡 运行以下命令重新登录：cd crawler && python3 xhs_login_helper.py
```

---

## 📅 定期维护建议

### 方案 A：按需更新（推荐）

- 当爬虫提示 Cookie 失效时，运行登录助手
- 适合手动运行爬虫的场景

### 方案 B：定期更新

在 crontab 中添加提醒任务：

```bash
# 每周一早上 8:00 检查 Cookie
0 8 * * 1 cd /path/to/echo_cms/crawler && python3 xhs_login_helper.py check || echo "小红书 Cookie 已过期，请更新"
```

### 方案 C：自动化登录（高级）

如果需要完全自动化，可以考虑：

1. **使用持久化浏览器会话**
   - Playwright 保存浏览器状态
   - 下次直接复用登录态

2. **接入验证码识别服务**
   - 自动识别短信验证码
   - 成本较高，适合企业场景

3. **使用小红书开放平台 API**
   - 官方 API，稳定可靠
   - 需要申请开发者权限

---

## 🛠️ 技术原理

### Cookie 提取流程

```
启动 Playwright 浏览器（非无头模式）
  ↓
访问 xiaohongshu.com
  ↓
等待用户手动登录（扫码/验证码）
  ↓
检测登录成功（查找用户头像元素）
  ↓
提取浏览器 Cookie（包括 HttpOnly）
  ↓
保存到 .env 文件
```

### 为什么不能用 document.cookie？

`web_session` 被设置为 **HttpOnly**，JavaScript 无法读取，必须通过浏览器 API 获取。

---

## 📊 Cookie 有效期说明

| Cookie 字段 | 作用 | 有效期 |
|------------|------|--------|
| `web_session` | 登录态标识 | 数小时到数天 |
| `a1` | 设备指纹 | 较长（数周） |
| `webId` | 设备 ID | 较长（数周） |

**关键字段**：`web_session` 和 `a1` 缺一不可。

---

## ❓ 常见问题

### Q1: 登录助手打开浏览器后无反应

**原因：** Playwright 浏览器驱动未安装

**解决：**
```bash
playwright install chromium
```

### Q2: 提示"未检测到登录"

**原因：** 登录成功但脚本未识别

**解决：** 按提示手动按 Enter 继续

### Q3: Cookie 保存后仍然失效

**原因：** 小红书检测到异常登录

**解决：**
1. 使用常用设备登录
2. 避免频繁切换 IP
3. 等待一段时间后重试

---

## 🔒 安全提示

1. **.env 文件已加入 .gitignore**，不会上传到 GitHub
2. **不要分享 Cookie**，包含你的登录态
3. **定期更新 Cookie**，降低账号风险
4. **使用小号**，避免主账号被封

---

## 📝 相关文件

- `xhs_login_helper.py` - 登录助手脚本
- `.env` - Cookie 配置文件（不上传 Git）
- `main.py` - 主爬虫（已集成自动检测）

