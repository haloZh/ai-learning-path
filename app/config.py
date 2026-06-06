import os

from dotenv import load_dotenv

load_dotenv()


def _first(*names: str, default: str = "") -> str:
    """按优先级返回第一个非空环境变量值。"""
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default


# LLM 配置:优先 VLLM_*(学院服务器 Qwen3-8B,与老师 .env 变量名一致),
# 回退通用 LLM_*,再回退旧 ARK_*(火山方舟)。三套命名都能用,迁移无痛。
LLM_API_KEY = _first("VLLM_API_KEY", "LLM_API_KEY", "ARK_API_KEY")
LLM_BASE_URL = _first(
    "VLLM_BASE_URL", "LLM_BASE_URL", "ARK_BASE_URL",
    default="https://ark.cn-beijing.volces.com/api/v3",
)
LLM_MODEL = _first(
    "VLLM_MODEL_NAME", "LLM_MODEL", "ARK_MODEL",
    default="doubao-seed-2-0-lite-260215",
)

# 是否使用 OpenAI response_format=json_object。vLLM 较新版支持;
# 若后端不支持(报错),设 LLM_JSON_MODE=false 改走 prompt 强约束 + 解析容错。
LLM_JSON_MODE = _first("LLM_JSON_MODE", default="true").lower() not in ("false", "0", "no")

# temperature:Qwen 推荐 0.0 更稳定;默认沿用 0.3
try:
    LLM_TEMPERATURE = float(_first("VLLM_TEMPERATURE", "LLM_TEMPERATURE", default="0.3"))
except ValueError:
    LLM_TEMPERATURE = 0.3

# ===== 向后兼容别名(旧代码引用 ARK_* 仍可用) =====
ARK_API_KEY = LLM_API_KEY
ARK_BASE_URL = LLM_BASE_URL
ARK_MODEL = LLM_MODEL

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
