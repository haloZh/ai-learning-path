"""LLM 占位生成 resources:为每个还没有资源的 concept 各生成 1 条学习资源。

为答辩演示阶段提供资源池,RAG 检索能从空到有,plan Agent 也能引用真实资源标题。
人工同学后续录入真实资源时按 (title, url) 去重,这些占位会被覆盖或并存。

LLM 不可用时(未配置 / 模型未开通 / 超时)自动降级到本地启发式 mock 生成,
保证脚本始终能跑出资源池,不会因 LLM 故障而全部 FAIL。

用法:
    .venv/bin/python -m scripts.seed_resources [--all] [--mock]

默认只为"尚无资源的 concept"生成;加 --all 则给所有 concept 强制再生一条。
加 --mock 则强制全部走本地兜底(不调 LLM,适合无网/无 key 环境快速铺数据)。
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


def _gen_one(concept: Concept) -> tuple[dict, str] | None:
    """返回 (资源 dict, 来源标记 'llm'|'mock');LLM 失败时降级到本地兜底。"""
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
            # LLM 返回了但字段不全,降级
            return _mock_one(concept), "mock"
        return {
            "title": title,
            "type": rtype,
            "estimated_minutes": mins,
            "summary": summary,
        }, "llm"
    except LLMUnavailable as e:
        print(f"  [WARN] LLM 不可用,降级 mock — {e}")
        return _mock_one(concept), "mock"


# 各模块默认资源形态:类型 + 标题后缀 + 时长
_MODULE_PRESET = {
    "算术": ("exercise", "专项精练", 20),
    "代数": ("video", "考点精讲", 25),
    "几何": ("video", "图解专项", 25),
    "数据分析": ("exercise", "题型突破", 20),
}


def _module_of(code: str) -> str:
    for m in _MODULE_PRESET:
        if code.startswith(m):
            return m
    return "代数"


def _mock_one(concept: Concept) -> dict:
    """本地启发式占位:依据知识点名与所属模块生成一条确定性资源。

    不调用任何外部服务,LLM 不可用时也能铺出可用的资源池。
    """
    module = _module_of(concept.code)
    rtype, suffix, mins = _MODULE_PRESET[module]
    name = concept.name or concept.code.split("-")[-1]
    title = f"{name}{suffix}"
    desc = (concept.description or "").strip()
    summary = (
        f"针对「{name}」的{suffix},覆盖该知识点的核心解题方法与常见易错点。"
        + (f"重点包括:{desc}" if desc else "适合管综数学备考阶段的针对性强化。")
    )
    return {
        "title": title[:22],
        "type": rtype,
        "estimated_minutes": mins,
        "summary": summary[:80],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="给所有 concept 强制生成(忽略已有)")
    parser.add_argument("--mock", action="store_true", help="强制全部走本地兜底,不调 LLM")
    args = parser.parse_args(argv[1:])

    init_db()
    inserted_llm = 0
    inserted_mock = 0
    skipped = 0

    with SessionLocal() as db:
        concepts = db.query(Concept).order_by(Concept.code).all()
        for c in concepts:
            existing = db.query(Resource).filter(Resource.concept_code == c.code).count()
            if existing > 0 and not args.all:
                skipped += 1
                continue

            print(f"[gen] {c.code} ...", end=" ", flush=True)
            if args.mock:
                data, source = _mock_one(c), "mock"
            else:
                data, source = _gen_one(c)

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
            if source == "llm":
                inserted_llm += 1
            else:
                inserted_mock += 1
            tag = "OK" if source == "llm" else "OK(mock)"
            print(f"{tag} — {data['title']} ({data['estimated_minutes']}min)")

    total = inserted_llm + inserted_mock
    print()
    print(
        f"[OK] 新增 {total} 条(LLM {inserted_llm} / mock 兜底 {inserted_mock})"
        f",跳过(已有) {skipped} 条"
    )
    if inserted_mock and not args.mock:
        print("提示:本次有资源走了 mock 兜底,说明 LLM 不可用(检查 ARK_API_KEY / 模型是否开通)")
    print("提示:跑完后运行 `.venv/bin/python -m scripts.init_rag` 重建向量索引")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
