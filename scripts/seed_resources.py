"""LLM 占位生成 resources:为每个还没有资源的 concept 各生成 1 条学习资源。

为答辩演示阶段提供资源池,RAG 检索能从空到有,plan Agent 也能引用真实资源标题。
人工同学后续录入真实资源时按 (title, url) 去重,这些占位会被覆盖或并存。

用法:
    .venv/bin/python -m scripts.seed_resources [--all]

默认只为"尚无资源的 concept"生成;加 --all 则给所有 concept 强制再生一条。
执行后请跑 .venv/bin/python -m scripts.init_rag 重建向量索引。
"""

from __future__ import annotations

import argparse
import os
import sys

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from app.agents.llm import LLMUnavailable, chat_json  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.models import Concept, Resource  # noqa: E402

_SYSTEM = """你是管综数学教研员,任务是为一个知识点生成 1 条占位学习资源。

输出严格 JSON,字段:
- title: string,资源标题,中文 ≤ 22 字,体现具体动作("分式方程系数化简专项练习"比"分式方程视频"好)
- type: string,从 [video, article, exercise, note] 任选 1
- estimated_minutes: integer 8-60,建议学习分钟
- summary: string,中文 ≤ 80 字,真实涵盖该知识点的子点和讲解方法,**不要重复 title**
"""


def _build_user(concept: Concept) -> str:
    parts = [
        f"知识点编码: {concept.code}",
        f"知识点名称: {concept.name}",
    ]
    if concept.description:
        parts.append(f"内容描述: {concept.description}")
    parts.append("请输出该知识点 1 条占位学习资源的 JSON。")
    return "\n".join(parts)


def _gen_one(concept: Concept) -> dict | None:
    try:
        result = chat_json(_SYSTEM, _build_user(concept))
        title = str(result.get("title", "")).strip()
        rtype = str(result.get("type", "")).strip().lower()
        summary = str(result.get("summary", "")).strip()
        try:
            mins = int(result.get("estimated_minutes", 20))
        except (TypeError, ValueError):
            mins = 20
        mins = max(8, min(60, mins))
        if rtype not in ("video", "article", "exercise", "note"):
            rtype = "article"
        if not title or not summary:
            return None
        return {
            "title": title,
            "type": rtype,
            "estimated_minutes": mins,
            "summary": summary,
        }
    except LLMUnavailable as e:
        print(f"  [WARN] {concept.code}: LLM 调用失败 — {e}")
        return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="给所有 concept 强制生成(忽略已有)")
    args = parser.parse_args(argv[1:])

    init_db()
    inserted = 0
    skipped = 0
    failed = 0

    with SessionLocal() as db:
        concepts = db.query(Concept).order_by(Concept.code).all()
        for c in concepts:
            existing = db.query(Resource).filter(Resource.concept_code == c.code).count()
            if existing > 0 and not args.all:
                skipped += 1
                continue

            print(f"[gen] {c.code} ...", end=" ", flush=True)
            data = _gen_one(c)
            if data is None:
                print("FAIL")
                failed += 1
                continue

            db.add(
                Resource(
                    concept_code=c.code,
                    title=data["title"],
                    type=data["type"],
                    estimated_minutes=data["estimated_minutes"],
                    summary=data["summary"],
                    url=None,
                )
            )
            db.commit()
            inserted += 1
            print(f"OK — {data['title']} ({data['estimated_minutes']}min)")

    print()
    print(f"[OK] 新增 {inserted} 条,跳过(已有) {skipped} 条,失败 {failed} 条")
    print("提示:跑完后运行 `.venv/bin/python -m scripts.init_rag` 重建向量索引")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
