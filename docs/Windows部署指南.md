# AI 个性化学习路径系统 — Windows 部署指南

**版本**：v1.0 · 2026-05-26  
**项目**：ai-learning-path（北科大 MBA 人工智能课 L-2 作业）  
**仓库**：https://github.com/haloZh/ai-learning-path

---

## 1. 运行环境要求

| 组件 | 最低版本 | 推荐版本 | 说明 |
|---|---|---|---|
| Windows | 10 (1909+) | 11 | 均可运行 |
| Python | 3.11 | 3.12 | 必须 64-bit |
| Node.js | 20 LTS | 22 LTS | 构建前端 |
| Git for Windows | 2.40+ | 最新版 | 含 Git Bash |
| 磁盘空间 | 5 GB | 8 GB | bge-m3 模型约 2.3 GB |
| 内存 | 8 GB | 16 GB | 首次加载 RAG 模型 |

> **网络说明**：bge-m3 模型通过国内镜像（hf-mirror.com）下载，首次初始化需科学上网或保持网络畅通。

---

## 2. 第一步：安装基础软件

### 2.1 安装 Python 3.12

1. 访问 https://python.org/downloads/，下载 **Windows installer (64-bit)**。
2. 运行安装程序，**务必勾选** "Add python.exe to PATH"。
3. 安装完成后，打开 PowerShell 验证：

```powershell
python --version
# 应输出：Python 3.12.x
```

### 2.2 安装 Node.js 22 LTS

1. 访问 https://nodejs.org/，下载 **22.x LTS** Windows 安装包。
2. 一路默认安装即可。
3. 验证：

```powershell
node --version
# 应输出：v22.x.x
npm --version
```

### 2.3 安装 Git for Windows

1. 访问 https://git-scm.com/downloads，下载 Windows 版。
2. 安装时推荐：
   - Line ending：选 "Checkout as-is, commit Unix-style"
   - Terminal：选 "Use Windows' default console window"（即 PowerShell）
3. 验证：

```powershell
git --version
# 应输出：git version 2.x.x.windows.x
```

---

## 3. 第二步：获取代码

### 3.1 配置 SSH 密钥（推荐）

```powershell
# 生成密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 查看公钥内容（复制到 GitHub → Settings → SSH Keys）
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

### 3.2 克隆仓库

```powershell
# 切换到工作目录，例如桌面
cd "$env:USERPROFILE\Desktop"

# SSH 克隆（需已配置密钥）
git clone git@github.com:haloZh/ai-learning-path.git

# 或 HTTPS 克隆（需 GitHub 账号）
git clone https://github.com/haloZh/ai-learning-path.git

# 进入项目目录
cd ai-learning-path
```

---

## 4. 第三步：配置 Python 虚拟环境

```powershell
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（PowerShell）
.venv\Scripts\Activate.ps1

# 如果提示"执行策略"限制，先执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# 然后重新激活

# 激活成功后命令提示符前缀应显示 (.venv)
```

> **注意**：后续所有命令均在已激活虚拟环境的 PowerShell 中执行。

### 安装 Python 依赖

```powershell
pip install -r requirements.txt
```

> 安装过程约 3–5 分钟，主要包含 FastAPI、LangGraph、SQLAlchemy、Chroma、sentence-transformers 等。

---

## 5. 第四步：配置环境变量

```powershell
# 复制配置模板
copy .env.example .env

# 用记事本或 VSCode 打开编辑
notepad .env
```

`.env` 文件关键字段说明：

| 字段 | 说明 | 示例值 |
|---|---|---|
| `ARK_API_KEY` | 火山方舟 API 密钥（必填） | `your-key-here` |
| `ARK_BASE_URL` | 方舟 API 地址（已预填） | `https://ark.cn-beijing.volces.com/api/v3` |
| `ARK_MODEL` | 模型 ID（已预填） | `ep-xxxxx-xxxxx` |

> **获取火山方舟 API Key**：登录 https://console.volcengine.com/ark，创建推理接入点，复制 Endpoint ID 填入 `ARK_MODEL`，API Key 填入 `ARK_API_KEY`。

---

## 6. 第五步：初始化数据库

```powershell
# 1. 导入知识点概念（约 20 条，秒级完成）
python -m scripts.seed_concepts

# 2. 导入题目数据（替换为实际 xlsx 路径）
python -m scripts.import_questions "C:\Users\你的名字\Desktop\math_questions.xlsx"

# 3. 生成学习资源（调用 LLM，约 1–2 分钟）
python -m scripts.seed_resources
```

---

## 7. 第六步：初始化 RAG 向量库

> 此步骤首次运行需下载 bge-m3 模型（2.3 GB），请确保网络畅通。

```powershell
# 设置国内镜像加速下载（本次 PowerShell 会话有效）
$env:HF_ENDPOINT = "https://hf-mirror.com"

# 初始化 RAG（首次约 10–20 分钟，之后秒级）
python -m scripts.init_rag
```

模型下载后缓存在 `%USERPROFILE%\.cache\huggingface\`，后续无需重复下载。

---

## 8. 第七步：构建前端

```powershell
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 返回项目根目录
cd ..
```

构建产物在 `frontend/dist/`，已配置 FastAPI 自动托管，无需额外部署。

---

## 9. 第八步：启动服务

```powershell
python -m uvicorn app.main:app --port 8000
```

启动成功后输出：

```
INFO:     Started server process [xxxx]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

打开浏览器访问：**http://localhost:8000**

---

## 10. 常见问题

### Q1：激活虚拟环境时提示"无法加载文件…因为在此系统上禁止运行脚本"

```powershell
# 以管理员身份运行 PowerShell，执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

### Q2：pip install 时 `sentence-transformers` 安装失败

通常是 C++ 编译工具缺失，安装 **Microsoft C++ Build Tools**：

1. 访问 https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. 下载并安装，勾选 "Desktop development with C++"
3. 重新运行 `pip install -r requirements.txt`

### Q3：init_rag 下载速度极慢

```powershell
# 确认镜像已设置
echo $env:HF_ENDPOINT
# 应输出：https://hf-mirror.com

# 若仍慢，尝试手动设置代理后重试
```

### Q4：`import_questions` 提示文件路径错误

Windows 路径中请使用反斜杠，或用引号括起含空格的路径：

```powershell
python -m scripts.import_questions "D:\学习资料\题目数据.xlsx"
```

### Q5：LLM 调用超时，系统降级到 mock 模式

这是正常的兜底机制。解决方法：

1. 检查 `.env` 中 `ARK_API_KEY` 是否正确填写。
2. 演示前 **提前 5 分钟预热**：访问一次 `/diagnose` 接口，让 LLM 冷启动完成。
3. 如确认 API Key 正确但仍超时，可稍等片刻后重试（方舟偶发限速）。

### Q6：页面提示 404 或无法打开

- 确认已执行 `npm run build`，且 `frontend/dist/` 目录存在。
- 确认服务在 8000 端口运行（未被防火墙拦截）。
- 尝试关闭 Windows Defender 防火墙对 8000 端口的限制。

---

## 11. 目录结构说明

```
ai-learning-path/
├── app/                  # FastAPI 后端
│   ├── agents/           # LangGraph 4-Agent 流水线
│   ├── evaluation/       # 客观指标计算
│   ├── models.py         # SQLAlchemy 数据模型（8张表）
│   └── main.py           # API 路由入口
├── frontend/             # Vue 3 + Vite 前端
├── scripts/              # 数据初始化脚本
├── docs/                 # 文档（含本文件）
├── reports/              # 评估回归报告
├── .env.example          # 环境变量模板
└── requirements.txt      # Python 依赖列表
```

---

## 12. 快速启动检查清单

| 步骤 | 命令 / 操作 | 完成 |
|---|---|---|
| 安装 Python 3.12 | `python --version` 验证 | ☐ |
| 安装 Node.js 22 | `node --version` 验证 | ☐ |
| 克隆仓库 | `git clone ...` | ☐ |
| 创建并激活虚拟环境 | `.venv\Scripts\Activate.ps1` | ☐ |
| 安装 Python 依赖 | `pip install -r requirements.txt` | ☐ |
| 配置 `.env` 填入 API Key | `notepad .env` | ☐ |
| 初始化数据库 | `seed_concepts` + `import_questions` + `seed_resources` | ☐ |
| 初始化 RAG 向量库 | `init_rag`（首次需下载模型） | ☐ |
| 构建前端 | `npm install && npm run build` | ☐ |
| 启动服务 | `uvicorn app.main:app --port 8000` | ☐ |
| 访问页面 | http://localhost:8000 | ☐ |

---

*如遇问题，可参考项目 README 或联系开发团队。*
