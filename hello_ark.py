"""第一步：验证方舟 API 能通。跑通此脚本说明 key/网络/模型名都对。"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("ARK_API_KEY")
base_url = os.getenv("ARK_BASE_URL")
model = os.getenv("ARK_MODEL")

missing = [name for name, val in [("ARK_API_KEY", api_key), ("ARK_BASE_URL", base_url), ("ARK_MODEL", model)] if not val]
if missing:
    print(f"[FAIL] .env 缺少变量: {', '.join(missing)}")
    sys.exit(1)

print(f"[INFO] base_url = {base_url}")
print(f"[INFO] model    = {model}")
print(f"[INFO] api_key  = {api_key[:8]}...{api_key[-4:]}")
print()

client = OpenAI(api_key=api_key, base_url=base_url)

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "你是一个个性化学习路径规划助手。"},
        {"role": "user", "content": "请用一句话介绍你能帮学生做什么。"},
    ],
)

print("[OK] 模型回复:")
print(response.choices[0].message.content)
print()
print(f"[USAGE] prompt={response.usage.prompt_tokens} completion={response.usage.completion_tokens} total={response.usage.total_tokens}")
