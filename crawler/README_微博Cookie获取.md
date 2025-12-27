# 微博 Cookie 获取指南

## 为什么需要 Cookie？

微博移动版 API 需要登录态才能访问用户数据，Cookie 是身份认证的凭证。

## 获取步骤

### 方法一：Chrome 浏览器（推荐）

1. **打开微博移动版**
   - 访问：https://m.weibo.cn/
   - 登录你的微博账号

2. **打开开发者工具**
   - 按 `F12` 或 `Cmd+Option+I` (Mac)
   - 切换到 **Network（网络）** 标签

3. **刷新页面**
   - 按 `F5` 或 `Cmd+R` 刷新页面
   - 在网络请求列表中找到任意一个请求（通常是 `getIndex` 开头的）

4. **复制 Cookie**
   - 点击该请求
   - 在右侧面板找到 **Request Headers（请求头）**
   - 找到 `Cookie:` 这一行
   - 复制整个 Cookie 字符串（从第一个字符到最后，不包括 `Cookie:` 本身）

5. **配置到项目**
   - 打开项目根目录的 `.env` 文件（如果不存在则创建）
   - 添加以下内容：
   ```
   WEIBO_COOKIE="你复制的Cookie字符串"
   ```

### 方法二：Safari 浏览器

1. 打开 Safari 开发菜单（偏好设置 → 高级 → 显示开发菜单）
2. 访问 https://m.weibo.cn/ 并登录
3. 开发 → 显示网页检查器
4. 切换到网络标签
5. 刷新页面，找到请求，复制 Cookie

## Cookie 示例

```
Cookie: SUB=_2A25xxx...; SUBP=0033xxx...; _T_WM=xxx...
```

**注意：** 
- Cookie 是一长串字符，包含多个键值对，用分号分隔
- 完整复制，不要遗漏任何部分
- Cookie 包含敏感信息，不要分享给他人

## 有效期

- 微博 Cookie 通常有效期为 **3-6 个月**
- 如果抓取失败，检查日志中是否有 "Cookie 已失效" 的提示
- 失效后重新按上述步骤获取新的 Cookie

## 测试 Cookie 是否有效

运行测试脚本：

```bash
cd crawler
python3 fetchers/weibo.py
```

如果输出用户信息和微博列表，说明 Cookie 有效。

## 常见问题

### Q: Cookie 太长了，怎么复制？
A: 在开发者工具中，右键点击 Cookie 值 → Copy Value，会自动复制完整内容。

### Q: 提示 "Cookie 未配置"？
A: 检查 `.env` 文件是否存在，格式是否正确（注意引号）。

### Q: 提示 "获取用户信息失败"？
A: Cookie 可能已失效，重新获取新的 Cookie。

### Q: 会不会被封号？
A: 正常使用不会。本项目每天只抓取一次，频率很低，且使用的是官方 API。

## 安全提示

- ⚠️ **不要将 `.env` 文件提交到 Git**（已在 `.gitignore` 中排除）
- ⚠️ **不要在公开场合分享 Cookie**
- ⚠️ 如果 Cookie 泄露，请立即修改微博密码


