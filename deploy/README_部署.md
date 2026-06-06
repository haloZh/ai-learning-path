# 阿里云服务器部署指南（Linux + 本地千问 Qwen3-8B）

> 把 AI 个性化学习路径系统部署到学校阿里云服务器，用学院本地 vLLM Qwen3-8B 做 LLM，HTTP+IP 访问。

---

## 〇、前置信息

| 项 | 值 |
|----|-----|
| LLM 后端 | 学院服务器 vLLM **Qwen3-8B** |
| 千问 endpoint | `http://<千问机内网IP>:9002/v1`（阿里云与千问机同内网直通） |
| 模型名 | `Qwen3-8B` |
| api_key | `sk-anything`（vLLM 占位，不校验） |
| 访问方式 | `http://<阿里云服务器公网IP>:8000` |

> ⚠️ 部署前确认：在阿里云服务器上能 `curl http://<千问机内网IP>:9002/v1/models` 通，否则 LLM 连不上（会自动降级 mock）。

---

## 一、传代码与数据到服务器

在**本地**执行（把项目和数据传上去；不含 .venv/node_modules）：

```bash
# 方式一:git clone（推荐，代码干净）
ssh <user>@<服务器IP>
git clone git@github.com:haloZh/ai-learning-path.git
cd ai-learning-path

# 然后单独把数据库和向量索引传上去(本地执行):
scp -r data/app.db <user>@<服务器IP>:~/ai-learning-path/data/
scp -r data/chroma <user>@<服务器IP>:~/ai-learning-path/data/
```

> data/ 被 .gitignore 排除，所以 git clone 后没有数据库和向量索引，必须 scp 单独传。
> 不传的话首次启动会建空库，没有题目/知识点，需自己跑 `python -m scripts.seed_concepts` 等脚本重建。

---

## 二、一键安装

```bash
cd ~/ai-learning-path
bash deploy/install.sh
```

脚本会：建 venv → pip 装后端依赖（清华镜像）→ npm 构建前端 → 生成 .env。

> 若提示缺 python3-venv：`sudo apt install python3-venv python3-pip`
> 若 bge-m3 模型下载慢/失败：脚本已设 HF_ENDPOINT 镜像；服务器若无公网，需从本地
> `~/.cache/huggingface/hub/models--BAAI--bge-m3` 打包 scp 到服务器同路径。

---

## 三、配置 .env

```bash
nano .env
```

填入千问地址（其余保持默认）：

```ini
VLLM_BASE_URL=http://<千问机内网IP>:9002/v1
VLLM_MODEL_NAME=Qwen3-8B
VLLM_API_KEY=sk-anything
VLLM_TEMPERATURE=0.0
LLM_JSON_MODE=true     # 若调用报 response_format 不支持，改 false
```

---

## 四、测试启动（前台，验证用）

```bash
./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- 等待日志出现 `RAG 预热完成 xxx ms`（首次 30-165 秒，加载 bge-m3）
- 另开终端测：`curl http://127.0.0.1:8000/health` → `{"status":"ok"}`
- **`--host 0.0.0.0` 必须有**，否则只能本机访问

---

## 五、开放端口（关键！最常见的访问不了原因）

阿里云控制台 → ECS 实例 → **安全组** → 配置规则 → 入方向 → 添加：
- 端口范围 `8000/8000`，授权对象 `0.0.0.0/0`（或限定来源 IP）
- 若服务器有系统防火墙：`sudo ufw allow 8000`（Ubuntu）

然后浏览器访问：**http://<阿里云服务器公网IP>:8000**

---

## 六、正式部署（常驻 + 开机自启）

用 systemd 让服务后台常驻、崩溃自动重启、关 SSH 不掉。

```bash
# 1) 改 service 文件里的 User / WorkingDirectory / ExecStart 为实际路径
nano deploy/learning-path.service

# 2) 安装并启动
sudo cp deploy/learning-path.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now learning-path

# 3) 查看状态与日志
systemctl status learning-path
journalctl -u learning-path -f
```

改代码后重启：`sudo systemctl restart learning-path`

---

## 七、（可选）用 80 端口 / 加 HTTPS

见 `deploy/nginx.conf.example`。先 HTTP+IP 阶段可跳过。

---

## 八、排错

| 现象 | 原因 / 解决 |
|------|------------|
| 浏览器打不开 | ①安全组没放行 8000 ②uvicorn 没用 `--host 0.0.0.0` |
| 诊断结果显示 "Mock 兜底" | LLM 没连上。在服务器 `curl http://<千问IP>:9002/v1/models` 确认通；查 .env 地址 |
| 调用报 `response_format` 不支持 | .env 设 `LLM_JSON_MODE=false`，重启服务 |
| 诊断很慢/卡住 | 首次 bge-m3 加载 1-2 分钟；单次诊断 30-40s 属正常 |
| 输出夹带思考过程导致解析失败 | 代码已处理 `<think>` 标签和 markdown 包裹；仍异常看 `journalctl` 日志 |
