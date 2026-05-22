"""初始化 / 重建 RAG 索引:把 resources 表全量写入 Chroma 向量库。

用法:
    .venv/bin/python -m scripts.init_rag

行为:
- 首次运行会触发 bge-m3 模型下载(~2.3 GB,走 hf-mirror 约 3-10 分钟);
- 之后每次运行做一次全量 upsert,resources 表无内容时输出 0 条;
- Chroma 库默认存于 ./data/chroma/(已被 .gitignore 忽略)。

可重复跑;每次写入按 resource_id 做 upsert。
"""

from __future__ import annotations

import os

# 默认走国内镜像加速 huggingface 下载,可被外部环境变量覆盖
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from app.agents.rag import RagUnavailable, get_rag  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402


def main() -> int:
    init_db()
    rag = get_rag()
    try:
        with SessionLocal() as db:
            n = rag.bootstrap_index(db)
        print(f"[OK] Chroma 索引已重建,写入 {n} 条资源")
        return 0
    except RagUnavailable as e:
        print(f"[ERR] RAG 不可用: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
