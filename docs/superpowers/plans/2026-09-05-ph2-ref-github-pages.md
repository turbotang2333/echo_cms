# PH2 裂变页 GitHub Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将二阶段招募裂变页面部署准备为 `echo_cms` 的静态子页面，并使其从独立公开脱敏数据仓库读取快照。

**Architecture:** `echo_cms/public/ph2-ref/` 持有静态页面并随 GitHub Pages 发布。Mac 本地导出器将经校验的快照写入独立 `ph2-ref-data` 仓库，页面通过公开 raw 地址按需拉取，不触发整站重建。

**Tech Stack:** Vite public assets、HTML/CSS/ES modules、Node built-in test runner、Python 标准库、zsh、macOS LaunchAgent、Git。

**Spec:** `docs/superpowers/specs/2026-09-05-ph2-ref-github-pages-design.md`

## Global Constraints

- 页面路径为 `/ph2-ref/`，页面名为“二阶段招募裂变”。
- 页面资源使用相对路径；快照刷新间隔为 300 秒，本地导出间隔为 600 秒。
- 公开数据仅包含匿名节点、分钟级时间、尾号四位/未知和匿名上级关系。
- 不提交凭据、数据库配置、完整手机号、内部记录标识或问卷答案。
- 不提交、推送或触发 GitHub Pages，除非用户在当前对话明确要求。

---

### Task 1: 添加可测试的 GitHub Pages 静态子页面

**Files:**
- Create: `test/ph2-ref-page.test.mjs`
- Create: `public/ph2-ref/index.html`
- Create: `public/ph2-ref/assets/app.js`
- Create: `public/ph2-ref/assets/styles.css`
- Create: `public/ph2-ref/assets/config.js`
- Create: `public/ph2-ref/data/phase-2-referral.json`

**Interfaces:**
- Consumes: `window.PH2_REF_DATA_URL` 和公开快照 `{ generatedAt, nodes }`。
- Produces: `/ph2-ref/` 可独立加载的页面，失败后保留现有图形。

- [ ] **Step 1: 写失败测试**

```js
test('ph2-ref page uses only relative local assets and a configurable public data URL', () => {
  const html = readFileSync('public/ph2-ref/index.html', 'utf8')
  const app = readFileSync('public/ph2-ref/assets/app.js', 'utf8')
  assert.match(html, /\.\/assets\/styles\.css/)
  assert.match(html, /\.\/assets\/config\.js/)
  assert.match(html, /\.\/assets\/app\.js/)
  assert.match(app, /300_000/)
  assert.match(app, /cache: 'no-store'/)
})
```

- [ ] **Step 2: 运行测试，确认因页面文件缺失失败**

Run: `node --test test/ph2-ref-page.test.mjs`

Expected: failure that `public/ph2-ref/index.html` is absent.

- [ ] **Step 3: 实现最小静态页面**

将已验证时间轴页面的 HTML、样式和脚本移入 `public/ph2-ref/`，仅改动快照来源为 `window.PH2_REF_DATA_URL`，保留相对资源引用与失败保图逻辑。

- [ ] **Step 4: 运行页面测试和构建**

Run: `node --test test/ph2-ref-page.test.mjs && npm run build`

Expected: tests pass and `dist/ph2-ref/index.html` exists.

### Task 2: 将本地同步改为数据仓库更新准备

**Files:**
- Modify: `/Users/turbotang/code-project/echo-ph2-referral/scripts/sync_referral_data.sh`
- Modify: `/Users/turbotang/code-project/echo-ph2-referral/tests/test_sync_artifacts.py`
- Modify: `/Users/turbotang/code-project/echo-ph2-referral/README.md`

**Interfaces:**
- Consumes: 只读数据库输出、`PH2_REF_DATA_REPO_DIR` 和本地 HMAC salt。
- Produces: 已校验的 `latest.json`；数据未改变时不创建 Git 提交。

- [ ] **Step 1: 写失败测试**

```python
def test_sync_script_updates_data_repo_only_after_snapshot_export():
    script = (ROOT / 'scripts/sync_referral_data.sh').read_text()
    assert 'PH2_REF_DATA_REPO_DIR' in script
    assert 'latest.json' in script
    assert 'git diff --quiet' in script
    assert 'rsync' not in script
```

- [ ] **Step 2: 运行测试，确认当前 rsync 实现不符合新约定**

Run: `uv run pytest tests/test_sync_artifacts.py -q`

Expected: test failure because the script still uses server rsync.

- [ ] **Step 3: 最小实现**

导出成功后比较 `latest.json` 内容；仅有变化时复制到已存在的数据仓库工作区并准备 Git 更新。脚本不创建仓库、不读取或打印凭据，也不在无用户授权时执行推送。

- [ ] **Step 4: 运行同步工件和导出器测试**

Run: `uv run pytest -q && zsh -n scripts/sync_referral_data.sh`

Expected: all tests pass.

### Task 3: 本地预览与发布前核验

**Files:**
- Modify: `README.md`
- Modify: `/Users/turbotang/code-project/echo-ph2-referral/README.md`

**Interfaces:**
- Consumes: 本地静态站与示例公开快照。
- Produces: 可复验的本地预览步骤和发布前检查清单。

- [ ] **Step 1: 写失败检查**

```js
test('build contains the ph2-ref entry point', () => {
  assert.ok(existsSync('dist/ph2-ref/index.html'))
})
```

- [ ] **Step 2: 构建并验证**

Run: `npm run build && node --test test/ph2-ref-page.test.mjs`

Expected: `dist/ph2-ref/index.html` exists and tests pass.

- [ ] **Step 3: 补充文档**

说明页面仓库与数据仓库的职责、公开数据边界、Mac 定时任务的环境变量，以及“明确提交和推送后才会对外发布”。
