# React + Vite

## 二阶段招募裂变

`public/ph2-ref/` 是独立静态页面。Vite 构建时会原样复制为 `dist/ph2-ref/`，页面资源均使用相对路径。

页面只读取 `turbotang2333/ph2-ref-data` 仓库中的公开脱敏快照；该快照只能包含匿名节点、分钟级提交时间、手机号后四位（或“未知”）和匿名邀请关系。数据库访问与同步密钥只保留在本机定时任务中，绝不进入本仓库。

页面更新随 `main` 分支的 GitHub Pages 工作流发布；数据快照由独立仓库更新，因此不需要为每次数据变化重建整站。

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
