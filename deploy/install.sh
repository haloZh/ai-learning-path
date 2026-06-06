#!/usr/bin/env bash
# ============================================================
#  AI 个性化学习路径系统 — Linux 一键安装脚本
#  适用:阿里云服务器(Ubuntu / CentOS)
#  作用:建 venv -> 装后端依赖 -> 构建前端。装完后配 .env 再启动。
# ============================================================
set -e
cd "$(dirname "$0")/.."   # 切到项目根目录
ROOT="$(pwd)"
echo "项目根目录: $ROOT"

PYPI_MIRROR="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "============================================================"
echo "  [1/5] 检测 Python3"
echo "============================================================"
if ! command -v python3 >/dev/null 2>&1; then
  echo "  [X] 未找到 python3,请先安装 (Ubuntu: sudo apt install python3 python3-venv python3-pip)"
  exit 1
fi
python3 --version

echo "============================================================"
echo "  [2/5] 检测 Node.js"
echo "============================================================"
if ! command -v node >/dev/null 2>&1; then
  echo "  [X] 未找到 node,请先安装 Node.js 18+ (推荐 nvm 或 https://nodejs.org)"
  exit 1
fi
node --version

echo "============================================================"
echo "  [3/5] 创建虚拟环境并安装后端依赖"
echo "============================================================"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "  [OK] 已创建 .venv"
fi
./.venv/bin/python -m pip install --upgrade pip -i "$PYPI_MIRROR"
./.venv/bin/python -m pip install -r requirements.txt -i "$PYPI_MIRROR"
echo "  [OK] 后端依赖安装完成"

echo "============================================================"
echo "  [4/5] 构建前端 (ymy)"
echo "============================================================"
if [ -f "ymy/dist/index.html" ]; then
  echo "  [OK] ymy/dist 已存在,跳过(如需重建请先删除 ymy/dist)"
else
  cd ymy
  npm install
  npm run build
  cd ..
  echo "  [OK] 前端构建完成"
fi

echo "============================================================"
echo "  [5/5] 检查 .env"
echo "============================================================"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  [!] 已从 .env.example 生成 .env —— 请编辑填入千问配置:"
  echo "      VLLM_BASE_URL=http://<千问机内网IP>:9002/v1"
  echo "      VLLM_MODEL_NAME=Qwen3-8B"
else
  echo "  [OK] .env 已存在"
fi

echo ""
echo "============================================================"
echo "  安装完成!后续:"
echo "  1) 编辑 .env 填千问地址:  nano .env"
echo "  2) 测试启动:"
echo "     ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "  3) 正式部署(开机自启/常驻)见 deploy/README_部署.md 的 systemd 步骤"
echo "  4) 别忘了在阿里云控制台【安全组】放行 8000 端口入方向!"
echo "============================================================"
