# B站 Cookie 获取指南

## 为什么需要 Cookie？

B站的部分 API 需要登录态才能正常访问（避免风控机制），Cookie 是身份认证的凭证。

## 获取步骤

###方法：Chrome 浏览器（推荐）

1. **打开B站**
   - 访问：https://www.bilibili.com/
   - 登录你的B站账号

2. **打开开发者工具**
   - 按 `F12` 或 `Cmd+Option+I` (Mac)
   - 切换到 **Network（网络）** 标签

3. **访问任意UP主空间页**
   - 例如：https://space.bilibili.com/3546889188280924
   - 在网络请求列表中找到名为 `stat` 或 `space` 的请求

4. **复制 Cookie**
   - 点击该请求
   - 在右侧面板找到 **Request Headers（请求头）**
   - 找到 `Cookie:` 这一行
   - 复制整个 Cookie 字符串（从第一个字符到最后，不包括 `Cookie:` 本身）

5. **配置到项目**
   - 打开项目根目录的 `.env` 文件（如果不存在则创建）
   - 添加以下内容：
   ```
   BILIBILI_COOKIE="你复制的Cookie字符串"
   ```

## Cookie 示例

```
Cookie: buvid3=xxx; b_nut=1234567890; _uuid=xxx; buvid4=xxx; SESSDATA=xxx; bili_jct=xxx; DedeUserID=xxx; DedeUserID__ckMd5=xxx
```

**注意：** 
- Cookie 是一长串字符，包含多个键值对，用分号分隔
- 完整复制，不要遗漏任何部分
- Cookie 包含敏感信息，不要分享给他人
- 最重要的字段是 `SESSDATA`，确保包含它

## 有效期

- B站 Cookie 通常有效期为 **1-3 个月**
- 如果抓取失败，检查日志中是否有 "Cookie 已失效" 或 "风控校验失败" 的提示
- 失效后重新按上述步骤获取新的 Cookie

## 测试 Cookie 是否有效

运行测试脚本：

```bash
cd crawler
export BILIBILI_COOKIE="你的Cookie"
python3 fetchers/bilibili.py
```

如果输出用户信息和动态列表，说明 Cookie 有效。

## 常见问题

### Q: Cookie 太长了，怎么复制？
A: 在开发者工具中，右键点击 Cookie 值 → Copy Value，会自动复制完整内容。

### Q: 提示 "Cookie 未配置"？
A: 检查 `.env` 文件是否存在，格式是否正确（注意引号）。

### Q: 提示 "风控校验失败" 或 "获取数据失败"？
A: Cookie 可能已失效或不完整，重新获取新的 Cookie。确保包含 `SESSDATA` 字段。

### Q: 会不会被封号？
A: 正常使用不会。本项目每天只抓取一次，频率很低，且使用的是官方 API。

## 安全提示

- ⚠️ **不要将 `.env` 文件提交到 Git**（已在 `.gitignore` 中排除）
- ⚠️ **不要在公开场合分享 Cookie**
- ⚠️ 如果 Cookie 泄露，请立即修改B站密码

## 参考项目

本实现参考了 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 项目的B站爬虫实现方式。


