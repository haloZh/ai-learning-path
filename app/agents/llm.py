"""LLM 调用封装。

设计原则:
- 调用方拿到的要么是合法 dict,要么是 LLMUnavailable 异常,绝不返回 None 让 caller 多写分支。
- 兜底由 nodes.py 决定:捕获 LLMUnavailable -> 走 mock。
"""

import json
import logging
from typing import Any

from openai import APIError, APITimeoutError, OpenAI

from ..config import ARK_API_KEY, ARK_BASE_URL, ARK_MODEL

logger = logging.getLogger(__name__)

_PLACEHOLDER_KEYS = {"", "put-your-ark-api-key-here"}
# 单次调用 timeout:火山方舟偶尔会响应到 30-50s,放宽到 60s 减少误退化到 mock。
# 应用层 retries=1 → 最坏 120s 后兜底,在演示场景可接受;正常调用 5-15s。
_TIMEOUT_SECONDS = 60.0


class LLMUnavailable(Exception):
    """LLM 不可用(未配置 / 调用失败 / 解析失败),由 caller 决定降级策略。"""


def _client() -> OpenAI | None:
    if ARK_API_KEY in _PLACEHOLDER_KEYS:
        return None
    return OpenAI(api_key=ARK_API_KEY, base_url=ARK_BASE_URL, timeout=_TIMEOUT_SECONDS)


def chat_json(system: str, user: str, *, retries: int = 1) -> dict[str, Any]:
    """调 LLM 返回 JSON dict。失败抛 LLMUnavailable,由 caller 兜底。"""
    client = _client()
    if client is None:
        raise LLMUnavailable("ARK_API_KEY 未配置")

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=ARK_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            content = resp.choices[0].message.content or ""
            return json.loads(content)
        except (APITimeoutError, APIError) as e:
            last_err = e
            logger.warning("LLM call failed (attempt %d): %s", attempt + 1, e)
        except json.JSONDecodeError as e:
            last_err = e
            logger.warning("LLM returned non-JSON (attempt %d): %s", attempt + 1, e)

    raise LLMUnavailable(f"LLM 调用失败: {last_err}") from last_err
