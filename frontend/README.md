# 前端工程(Vue 3 + Vite)

L-2 个性化学习路径系统的前端工程。

---

## ⚠️ 当前状态(2026-05-25)

> 本目录内的 Vue 工程是 **AI 第一版临时实现**,功能完整但 UI 风格不理想。
> **接手做前端的同学,可以**:
>
> 1. **基于本工程改进** —— 保留 `src/api.js`、`src/store.js`、`src/utils/katex.js`,重做 `src/views/*.vue` 与样式;
> 2. **从零开始做** —— 删掉 `src/views`、`src/App.vue`、`src/assets/style.css`,自己起,保留 `package.json` / `vite.config.js` 即可。
>
> **API 对接细节、字段语义、关键陷阱、KaTeX 集成方式,全部见 [`../docs/前端对接文档.md`](../docs/前端对接文档.md)。开始做之前请通读一遍。**

---

## 技术栈

- Vue 3 + Vite 5 + Vue Router 4(hash 模式)
- KaTeX(题面 / 路径 / 解析里的 LaTeX 公式渲染)
- naive-ui(可换成你熟悉的 UI 库,如 Element Plus / Ant Design Vue / Tailwind 等)

## 启动

第一次拉代码后:

```bash
npm install
npm run dev      # 起开发服务器,默认 http://localhost:5173
```

后端开发服务器(另一个终端):

```bash
cd ..
.venv/bin/uvicorn app.main:app --port 8000 --reload
```

前端 dev server 已配 proxy:`/api/*` → `http://localhost:8000/*`,跨域无碍。

## 生产部署

```bash
npm run build    # 产物在 frontend/dist/
```

后端 `app/main.py` 已挂 `frontend/dist/` 到根路径,**起 uvicorn 8000 一个进程**就能 serve 前端 + 后端。

## 目录结构

```
frontend/
├── package.json
├── vite.config.js
├── index.html
└── src/
    ├── main.js              # 入口 + router 注册
    ├── App.vue              # 顶部步骤条 + router-view
    ├── api.js               # fetch 封装,统一对接后端
    ├── store.js             # 全局状态(reactive,无需 Pinia)
    ├── theme.js             # naive-ui 主题覆写
    ├── assets/style.css     # 全局样式
    ├── utils/katex.js       # KaTeX 渲染封装
    └── views/
        ├── ProfileView.vue   # ① 学生画像
        ├── DiagnoseView.vue  # ② 模拟答卷
        ├── PathView.vue      # ③ 诊断结果
        └── StudyView.vue     # ④ 学习交互
```

## 与后端的契约

**所有契约见 [`../docs/前端对接文档.md`](../docs/前端对接文档.md)**,包含:

- 9 个 API 端点详解
- 请求 / 响应字段表
- LaTeX 渲染、`mock` 兜底字段、`concept_id` vs `concept_code` 等 5 个关键陷阱
- 典型对接流程(profile → sample → diagnose → path → interaction)
- 错误处理约定
- Swagger UI / OpenAPI JSON 链接

也可以打开 http://localhost:8000/docs 看实时字段(以 Swagger 为准)。
