# 开发流程说明

## 脚本说明

### 生产环境脚本

#### `manual_crawl.bat` - 手动抓取(生产)
- **用途**: 手动触发数据抓取和部署
- **分支**: main (生产分支)
- **提交内容**: 仅数据文件 (`public/data.json`, `archive/`)
- **部署**: 触发 GitHub Actions 自动部署到生产环境
- **使用场景**: 日常数据更新

#### `daily_crawl.bat` - 定时抓取(生产)
- **用途**: 定时任务自动执行
- **分支**: main (生产分支)
- **提交内容**: 仅数据文件
- **部署**: 触发 GitHub Actions 自动部署
- **使用场景**: 每天自动更新数据

### 开发环境脚本

#### `dev_crawl.bat` - 开发测试
- **用途**: 开发新功能时测试数据结构
- **分支**: dev (开发分支)
- **提交内容**: 所有修改(代码 + 数据)
- **部署**: 不触发生产部署
- **使用场景**: 修改数据结构、测试新功能

---

## 完整开发流程

### 场景1: 日常数据更新(无代码修改)

```bash
# 直接运行生产脚本
双击 manual_crawl.bat

# 或等待定时任务自动执行
# 每天 9:00 AM 自动运行
```

**流程:**
1. 抓取数据
2. 提交数据到 main
3. 推送到 GitHub
4. 自动部署到生产环境
5. 1-3分钟后网站更新

---

### 场景2: 修改数据结构(需要改代码)

#### 步骤1: 创建开发分支

```bash
# 在项目根目录打开终端
git checkout -b dev

# 或者如果 dev 分支已存在
git checkout dev
```

#### 步骤2: 修改代码和数据结构

- 修改 `crawler/` 下的爬虫代码
- 修改 `src/` 下的前端代码
- 修改数据结构定义

#### 步骤3: 测试新数据结构

```bash
# 运行开发测试脚本
双击 dev_crawl.bat
```

**脚本会自动:**
1. 检查是否在 dev 分支(如果不是会提示切换)
2. 运行爬虫
3. 提交所有修改(代码 + 数据)
4. 推送到 dev 分支

#### 步骤4: 本地验证

```bash
# 启动本地开发服务器
npm run dev

# 访问 http://localhost:5173
# 验证新数据结构是否正常显示
```

#### 步骤5: 合并到生产

确认无误后:

```bash
# 切换到 main 分支
git checkout main

# 合并 dev 分支
git merge dev

# 推送到 GitHub(触发生产部署)
git push
```

#### 步骤6: 验证生产环境

- 等待 GitHub Actions 完成(1-3分钟)
- 访问生产网站验证

---

## 分支管理策略

### main 分支(生产)
- ✅ 稳定的代码
- ✅ 生产环境数据
- ✅ 触发自动部署
- ❌ 不要直接在 main 上开发新功能

### dev 分支(开发)
- ✅ 开发新功能
- ✅ 测试数据结构
- ✅ 实验性修改
- ❌ 不触发生产部署

---

## 常见问题

### Q1: 我在 dev 分支修改了代码,能直接运行 manual_crawl.bat 吗?

**不建议!** 
- `manual_crawl.bat` 会提交到 main 分支
- 如果你在 dev 分支,会导致混乱
- 应该使用 `dev_crawl.bat`

### Q2: 如果我忘记切换分支怎么办?

**不用担心!**
- `dev_crawl.bat` 会自动检查分支
- 如果不在 dev 分支,会提示你切换
- 可以选择自动切换或取消

### Q3: dev 分支的数据会影响生产环境吗?

**不会!**
- dev 分支的提交不会触发生产部署
- 只有 main 分支的推送才会部署
- dev 分支只用于本地测试

### Q4: 如何删除 dev 分支?

```bash
# 切换到 main
git checkout main

# 删除本地 dev 分支
git branch -d dev

# 删除远程 dev 分支
git push origin --delete dev
```

### Q5: 多人协作怎么办?

```bash
# 拉取最新的 dev 分支
git checkout dev
git pull origin dev

# 开发完成后推送
双击 dev_crawl.bat
```

---

## 快速参考

| 场景 | 使用脚本 | 分支 | 提交内容 | 是否部署 |
|------|---------|------|---------|---------|
| 日常数据更新 | `manual_crawl.bat` | main | 仅数据 | ✅ 是 |
| 定时自动更新 | `daily_crawl.bat` | main | 仅数据 | ✅ 是 |
| 开发新功能 | `dev_crawl.bat` | dev | 代码+数据 | ❌ 否 |

---

## 最佳实践

1. **保持 main 分支稳定** - 只合并经过测试的代码
2. **在 dev 分支开发** - 所有新功能都在 dev 上开发
3. **频繁提交** - 在 dev 分支上可以频繁提交,不影响生产
4. **测试后再合并** - 确保本地测试通过后再合并到 main
5. **定期同步** - 定期将 main 的更新合并到 dev

```bash
# 将 main 的更新同步到 dev
git checkout dev
git merge main
```

---

## 紧急回滚

如果生产环境出现问题:

```bash
# 查看提交历史
git log --oneline

# 回滚到上一个版本
git reset --hard HEAD~1

# 强制推送(谨慎使用!)
git push --force
```

**注意**: 强制推送会覆盖远程历史,请确保你知道自己在做什么!

---

## 需要帮助?

- 查看 Git 状态: `git status`
- 查看当前分支: `git branch`
- 查看提交历史: `git log --oneline --graph --all`
- 放弃本地修改: `git checkout .`
- 查看远程分支: `git branch -r`

