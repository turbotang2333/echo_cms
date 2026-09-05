# PH2 裂变页 GitHub Pages 设计

## 目标

在 `https://echo.turbotang.top/ph2-ref/` 提供“二阶段招募裂变”公开时间轴，并让页面约每五分钟读取一份约每十分钟更新的脱敏快照。

## 已确认边界

- `echo_cms` 是 React + Vite 项目，现有 `main` 分支通过 GitHub Pages 发布 `dist/`。
- 个人站子页面放在 `public/ph2-ref/`，构建时原样复制到 `dist/ph2-ref/`。
- 公开页面只展示 HMAC 节点标识、分钟级提交时间、手机号后四位（或“未知”）和匿名上级关系。
- 页面、数据仓库和日志不得包含完整手机号、数据库地址、凭据、邀请码、内部记录标识或问卷内容。
- 现有服务器镜像发布底座只支持域名级应用，不用于同域名的 `/ph2-ref/` 路径。

## 架构

```text
Mac + VPN + 只读数据库
  -> 本地导出器生成脱敏 latest.json（每 600 秒）
  -> 独立公开数据仓库 ph2-ref-data
  -> raw GitHub 数据地址
  -> echo_cms/public/ph2-ref/ 页面每 300 秒读取

echo_cms main
  -> GitHub Pages
  -> echo.turbotang.top/ph2-ref/
```

### 页面

- 复用已验证的纯静态时间轴页面，放入 `public/ph2-ref/`。
- 页面内部资源使用 `./` 相对路径，不受 Vite 当前 `/echo_cms/` base 设置影响。
- 页面每 300 秒请求公开快照；请求失败时保留已经绘制的图，并显示上次成功更新时间。
- JSON 地址集中在 `public/ph2-ref/assets/config.js`，默认使用将来数据仓库的 raw GitHub 地址。

### 数据

- 数据仓库名为 `turbotang2333/ph2-ref-data`，只包含 `latest.json` 和最小公开说明。
- Mac 本地同步脚本在导出器校验成功后，只有快照发生内容变化时才更新该仓库并推送。
- 首次创建仓库、向 GitHub 推送页面或数据属于发布动作，需在本地验证通过后单独执行。

## 失败处理

- VPN、数据库或导出失败：不更新公开数据仓库，页面继续使用上一次成功快照。
- 数据 URL 临时不可用：页面保留当前图，不清空图形。
- GitHub Pages 域名绑定或发布失败：不改变现有主站页面；仅记录发布失败原因后处理。

## 验收

1. `npm run build` 后生成 `dist/ph2-ref/index.html` 及其相对资源。
2. 页面代码不含数据库、凭据或完整手机号字段名。
3. 时间轴从公开数据地址读取并以五分钟间隔刷新。
4. 导出器的公开 JSON 合约测试仍通过，且同步脚本只在数据变化时准备数据仓库更新。
5. 本地静态预览可显示时间轴；发布后再验证 `https://echo.turbotang.top/ph2-ref/`。
