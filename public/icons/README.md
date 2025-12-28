# 游戏图标使用说明

## ✨ 约定优于配置

本项目采用**自动识别**机制，只需按规范命名图片文件并放入此目录，无需手动配置路径。

## 目录结构
将游戏图标图片文件放在此目录下：`public/icons/`

## 命名规范（重要）
**图片文件名必须与 `games_config.json` 中的游戏 `id` 完全一致**

**当前游戏列表：**
- `pengpeng.webp` → 夜幕之下（代号：砰砰）
- `lianren.webp` → 代号：恋人
- `ruyiqingtan.webp` → 如意情探
- `lengjing.webp` → 代号：棱镜
- `xingmian.webp` → 星眠
- `wuxiangu.webp` → 无限谷
- `sol.webp` → 代号：Sol
- `eve.webp` → EVE
- `breathofyou.webp` → Breath of You

## 支持格式
- WEBP (推荐，体积小、质量好)
- PNG (推荐，支持透明背景)
- JPG / JPEG
- GIF

## 图片要求
- **推荐尺寸：** 256x256 像素或更高（会自动缩放为 48x48px 显示）
- **建议比例：** 1:1 正方形
- **文件大小：** 建议每张图片不超过 500KB

## 使用方法

### 方式一：自动识别（推荐）
1. 按照游戏 `id` 命名图片文件（如 `pengpeng.webp`）
2. 放入 `public/icons/` 目录
3. 前端会自动加载，无需任何配置

### 方式二：手动指定
如果需要使用特殊路径或文件名，可以在 `games_config.json` 中手动配置：

```json
{
  "id": "pengpeng",
  "name": "夜幕之下（代号：砰砰）",
  "icon_url": "/icons/custom_name.png",  // 手动指定路径
  ...
}
```

## 智能回退机制
前端加载优先级：
1. **优先使用** `games_config.json` 中配置的 `icon_url`（如果有）
2. **自动尝试** 加载 `/icons/{游戏id}.webp`
3. **失败回退** 显示文字头像（游戏名首字）

## 添加新游戏图标
只需将新游戏的图标按 id 命名后放入此目录即可，例如：
- 添加新游戏 `id: "newgame"` → 放入 `newgame.webp` → 自动生效

