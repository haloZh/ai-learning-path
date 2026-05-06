# 前端工程（Vue 3 + Vite）

本目录是 L-2 个性化学习路径系统的前端工程。技术栈：**Vue 3 + Vite**，由前端同学维护。

## 初始化

第一次拉代码后，在本目录执行：

```bash
# 推荐 TypeScript 模板
npm create vite@latest . -- --template vue-ts

# 或纯 Vue 模板
npm create vite@latest . -- --template vue

npm install
npm run dev
```

默认会跑在 `http://localhost:5173`。

## 与后端联调

后端 FastAPI 跑在 `http://localhost:8000`，已自带：

- `/docs` — Swagger UI 接口文档
- `/openapi.json` — OpenAPI 规范，可用来生成 TS 类型

启动后端：

```bash
cd ..
.venv/bin/uvicorn app.main:app --reload
```

### 跨域

前端 5173 调后端 8000 默认会被浏览器拦截。后端已计划在 `app/main.py` 加 CORS 中间件：

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

如果开始联调时还没加，提醒后端同学补上。

### 推荐目录结构（仅供参考）

```
frontend/
├── src/
│   ├── api/          # 后端接口封装 (axios)
│   ├── views/        # 页面级组件
│   │   ├── ProfileView.vue    # 画像录入
│   │   ├── DiagnoseView.vue   # 诊断测验
│   │   ├── PathView.vue       # 学习路径视图
│   │   └── StudyView.vue      # 学习工作台
│   ├── components/   # 通用组件
│   ├── stores/       # Pinia 状态
│   └── router/       # Vue Router
├── package.json
└── vite.config.ts
```

## 设计参考

完整的前端四视图说明见 `../docs/产品方案.md` §3.1。
