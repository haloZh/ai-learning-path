#!/usr/bin/env bash
# ============================================================
#  离线安装脚本 — 用于无法联网的学院服务器
#  (Ubuntu 24.04 / Python 3.12 / x86_64)
#
#  前置:已通过 scp 把以下内容传到服务器项目目录:
#    - 项目代码(本仓库)
#    - offline_wheels/        ← GitHub Actions 产出的依赖 wheel 目录
#    - data/app.db, data/chroma/   ← 数据库与向量索引
#    - bge-m3-model/          ← 解压后的 bge-m3 模型目录
#    - ymy/dist/              ← 本地构建好的前端产物
#
#  用法:bash deploy/offline_install.sh
# ============================================================
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
echo "项目根目录: $ROOT"

WHEELS="$ROOT/offline_wheels"

echo "============================================================"
echo "  [1/4] 创建虚拟环境"
echo "============================================================"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "  [OK] 已创建 .venv"
else
  echo "  [OK] .venv 已存在"
fi

echo "============================================================"
echo "  [2/4] 离线安装 Python 依赖"
echo "============================================================"
if [ ! -d "$WHEELS" ]; then
  echo "  [X] 找不到 offline_wheels 目录!"
  echo "      请先把 GitHub Actions 产出的 wheel 包 scp 到 $WHEELS"
  exit 1
fi
# venv 自带 pip;离线安装,完全不联网
./.venv/bin/python -m pip install --no-index --find-links="$WHEELS" -r requirements.txt
echo "  [OK] 依赖离线安装完成"

echo "============================================================"
echo "  [3/4] 检查 bge-m3 模型"
echo "============================================================"
if [ -d "$ROOT/bge-m3-model" ] && [ -f "$ROOT/bge-m3-model/config.json" ]; then
  echo "  [OK] bge-m3 模型在 $ROOT/bge-m3-model"
  echo "       .env 里需配: EMBEDDING_MODEL_PATH=$ROOT/bge-m3-model"
else
  echo "  [!] 未找到 bge-m3-model 目录。RAG 将不可用(检索走空兜底)。"
  echo "      如需 RAG,把模型目录 scp 到 $ROOT/bge-m3-model"
fi

echo "============================================================"
echo "  [4/4] 检查 .env 与前端产物"
echo "============================================================"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  [!] 已生成 .env,请编辑填入(见下方提示)"
fi
if [ -f "ymy/dist/index.html" ]; then
  echo "  [OK] 前端产物 ymy/dist 就绪"
else
  echo "  [!] 缺 ymy/dist,需本地构建后 scp 上来(服务器无 Node 无法构建)"
fi

echo ""
echo "============================================================"
echo "  安装完成!接下来:"
echo "  1) 编辑 .env,确认以下配置:"
echo "       VLLM_BASE_URL=http://localhost:9002/v1"
echo "       VLLM_MODEL_NAME=Qwen3-8B"
echo "       VLLM_API_KEY=sk-anything"
echo "       LLM_JSON_MODE=true"
echo "       EMBEDDING_MODEL_PATH=$ROOT/bge-m3-model"
echo "  2) 启动(前台测试):"
echo "       ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8088"
echo "     注意:vLLM 已占用 8000,本项目用 8088(或其他空闲端口)"
echo "  3) 浏览器访问 http://<服务器IP>:8088"
echo "============================================================"
