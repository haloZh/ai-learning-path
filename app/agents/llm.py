"""LLM 调用封装。

设计原则:
- 调用方拿到的要么是合法 dict,要么是 LLMUnavailable 异常,绝不返回 None 让 caller 多写分支。
- 兜底由 nodes.py 决定:捕获 LLMUnavailable -> 走 mock。

多后端兼容:
- 火山方舟 Doubao / 学院服务器 vLLM Qwen3-8B / 任意 OpenAI 兼容端点。
- 配置见 config.py(VLLM_* > LLM_* > ARK_* 三级回退)。
- 本地千问可能不支持 response_format=json_object,或在输出夹带 ```json``` 代码块、
  Qwen3 的 <think>...</think> 思考片段 —— 由 _extract_json 统一容错。
"""

import json
import logging
import re
from typing import Any

from openai import APIError, APITimeoutError, OpenAI

from ..config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_JSON_MODE,
    LLM_MODEL,
    LLM_TEMPERATURE,
)

logger = logging.getLogger(__name__)

# 火山默认地址:base_url 仍是它且 key 为占位时,视为"未真正配置 LLM"
_DEFAULT_ARK_URL = "https://ark.cn-beijing.volces.com/api/v3"
_PLACEHOLDER_KEYS = {"", "put-your-ark-api-key-here", "your-ark-api-key-here"}

# 单次调用 timeout:本地千问 8B 推理 + 长 prompt 可能到 30-60s,放宽到 120s
_TIMEOUT_SECONDS = 120.0


class LLMUnavailable(Exception):
    """LLM 不可用(未配置 / 调用失败 / 解析失败),由 caller 决定降级策略。"""


def _is_configured() -> bool:
    """判断是否已配置可用的 LLM 端点。

    - 本地/自托管端点(base_url 非火山默认):即使 key 是 sk-anything/EMPTY 也算已配置。
    - 仍是火山默认地址:必须有真实 key 才算配置。
    """
    if LLM_BASE_URL and LLM_BASE_URL.rstrip("/") != _DEFAULT_ARK_URL.rstrip("/"):
        return True
    return LLM_API_KEY not in _PLACEHOLDER_KEYS


def _client() -> OpenAI | None:
    if not _is_configured():
        return None
    # 本地端点常用占位 key,openai SDK 要求 key 非空,给个默认值
    key = LLM_API_KEY or "sk-anything"
    return OpenAI(api_key=key, base_url=LLM_BASE_URL, timeout=_TIMEOUT_SECONDS)


def _extract_json(content: str) -> dict[str, Any]:
    """从 LLM 文本输出中稳健地提取 JSON 对象。

    处理:① Qwen3 的 <think>...</think> 思考片段 ② ```json ... ``` 代码块包裹
    ③ 前后多余文字。失败抛 JSONDecodeError 由上层兜底。
    """
    text = content.strip()
    # 去掉 <think>...</think>(Qwen3 思考模式)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    # 直接尝试
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 剥离 ```json ... ``` 或 ``` ... ``` 代码块
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", text, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 提取第一个 { 到最后一个 } 的片段
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    # 都失败,抛出让 caller 兜底
    return json.loads(text)


# 关闭 json_object 模式时,在 system prompt 末尾追加的强约束
_JSON_HINT = (
    "\n\n重要:只输出一个合法的 JSON 对象,不要输出任何解释文字、"
    "不要用 markdown 代码块包裹、不要输出思考过程。"
)


def chat_json(
    system: str,
    user: str,
    *,
    retries: int = 1,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """调 LLM 返回 JSON dict。失败抛 LLMUnavailable,由 caller 兜底。

    max_tokens: 限制输出长度。LLM 耗时主要随输出 token 数线性增长,
    给生成类节点(plan/evaluate)设上限可显著降低响应时间。
    """
    client = _client()
    if client is None:
        raise LLMUnavailable("LLM 未配置(base_url 为默认且 key 为占位)")

    system_msg = system if LLM_JSON_MODE else (system + _JSON_HINT)

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            kwargs: dict[str, Any] = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user},
                ],
                "temperature": LLM_TEMPERATURE,
            }
            if LLM_JSON_MODE:
                kwargs["response_format"] = {"type": "json_object"}
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            resp = client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or ""
            return _extract_json(content)
        except (APITimeoutError, APIError) as e:
            last_err = e
            logger.warning("LLM call failed (attempt %d): %s", attempt + 1, e)
        except json.JSONDecodeError as e:
            last_err = e
            logger.warning("LLM returned non-JSON (attempt %d): %s", attempt + 1, e)

    raise LLMUnavailable(f"LLM 调用失败: {last_err}") from last_err
