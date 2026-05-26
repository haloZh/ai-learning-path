"""批量回归评估:跑 N 次模拟诊断,聚合 5 项客观指标。

用途:
- 调 prompt / RAG / 模型版本前后对比(A/B),沉淀到 README 或答辩时给老师看
- 答辩被问"如何证明 RAG 准确率 / 路径合理"时拿数据回答

用法:
    .venv/bin/python -m scripts.run_eval [--n 5] [--mode mixed|wrong|right] [--out reports/eval_<时间戳>.md]

输出:Markdown 报告,含每次结果 + 聚合统计。
"""

from __future__ import annotations

import argparse
import os
import random
import statistics
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from app.agents import build_diagnose_graph  # noqa: E402
from app.agents.nodes import _get_prerequisites_for, _retrieve_resource_pool  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.evaluation import metrics  # noqa: E402
from app.models import Question, Student  # noqa: E402


def _sample_questions(db, n: int) -> list[Question]:
    all_q = db.query(Question).all()
    random.shuffle(all_q)
    seen: set[str] = set()
    out: list[Question] = []
    for q in all_q:
        if q.concept_code in seen:
            continue
        seen.add(q.concept_code)
        out.append(q)
        if len(out) >= n:
            break
    return out


def _fake_answer(q: Question, mode: str) -> bool:
    if mode == "wrong":
        return False
    if mode == "right":
        return True
    return random.random() < max(0.2, 1.0 - (q.difficulty or 1) * 0.15)


def _run_one(graph, student: Student, n: int, mode: str) -> dict:
    with SessionLocal() as db:
        questions = _sample_questions(db, n)

    answers = []
    for q in questions:
        answers.append({
            "question_id": q.id,
            "concept_id": q.concept_code,
            "correct": _fake_answer(q, mode),
            "seconds": random.randint(20, 200),
        })

    profile = {
        "subject": student.subject,
        "cognitive_level": student.cognitive_level,
        "learning_style": student.learning_style,
        "learning_goal": student.learning_goal,
        "available_minutes_per_day": student.available_minutes_per_day,
    }

    result = graph.invoke({
        "student_id": student.id,
        "student_profile": profile,
        "answers": answers,
        "reasoning": [],
        "used_mock": False,
    })

    mastery = result.get("mastery", {})
    path = result.get("path", [])
    resource_pool = result.get("resource_pool", {}) or _retrieve_resource_pool(mastery)
    prerequisites = _get_prerequisites_for(set(mastery.keys()))

    objective = metrics.all_metrics(
        path=path,
        mastery=mastery,
        prerequisites=prerequisites,
        resource_pool=resource_pool,
        budget_minutes=student.available_minutes_per_day or 60,
    )
    evaluation = result.get("evaluation") or {}

    return {
        "mock": result.get("used_mock", False),
        "n_answers": len(answers),
        "n_path": len(path),
        "objective": objective,
        "llm_score": evaluation.get("score"),
        "llm_summary": evaluation.get("summary"),
    }


def _aggregate(rows: list[dict]) -> dict[str, float]:
    keys = ["diversity", "prereq_violation", "resource_hit", "feasibility", "targeting"]
    agg = {}
    for k in keys:
        vals = [r["objective"][k] for r in rows]
        agg[f"{k}_mean"] = round(statistics.mean(vals), 3) if vals else 0
        agg[f"{k}_std"] = round(statistics.stdev(vals), 3) if len(vals) > 1 else 0.0
    llm = [r["llm_score"] for r in rows if r["llm_score"] is not None]
    agg["llm_score_mean"] = round(statistics.mean(llm), 1) if llm else None
    return agg


def _render_md(rows: list[dict], agg: dict, args) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# 评估回归报告 · {ts}",
        "",
        f"**配置**:n={args.n} 题/次,共 {args.runs} 次模拟,模式={args.mode}",
        "",
        "## 1. 客观指标(聚合)",
        "",
        "| 指标 | 均值 | 标准差 | 解读 |",
        "|---|---|---|---|",
        f"| 多样性 (diversity) | {agg['diversity_mean']} | ±{agg['diversity_std']} | 越接近 1 = 路径覆盖面广 |",
        f"| 先修违反率 (prereq_violation) | {agg['prereq_violation_mean']} | ±{agg['prereq_violation_std']} | 0 = 完全合规 |",
        f"| 资源命中率 (resource_hit) | {agg['resource_hit_mean']} | ±{agg['resource_hit_std']} | 越接近 1 = LLM 真用了 RAG |",
        f"| 可行性比值 (feasibility) | {agg['feasibility_mean']} | ±{agg['feasibility_std']} | < 1 = 在时间预算内 |",
        f"| 针对性 (targeting) | {agg['targeting_mean']} | ±{agg['targeting_std']} | 越接近 1 = 越聚焦薄弱点 |",
        "",
        f"**LLM 自评均分**:{agg.get('llm_score_mean', 'N/A')} / 100",
        "",
        "## 2. 单次明细",
        "",
        "| # | path | mock | targeting | prereq | resource_hit | feasibility | LLM | 总评 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        o = r["objective"]
        lines.append(
            f"| {i} | {r['n_path']} | {'✗' if r['mock'] else '✓'} | "
            f"{o['targeting']} | {o['prereq_violation']} | {o['resource_hit']} | "
            f"{o['feasibility']} | {r['llm_score'] or '-'} | "
            f"{(r['llm_summary'] or '')[:40]} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=5, help="每次抽题数")
    parser.add_argument("--runs", type=int, default=3, help="跑几次")
    parser.add_argument("--mode", choices=["wrong", "right", "mixed"], default="mixed")
    parser.add_argument("--student-id", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", type=str, default=None, help="报告输出路径")
    args = parser.parse_args(argv[1:])

    if args.seed is not None:
        random.seed(args.seed)

    with SessionLocal() as db:
        student = db.get(Student, args.student_id)
        if not student:
            print(f"[ERR] student_id={args.student_id} 不存在")
            return 1
    print(f"[run] student={student.nickname} (id={student.id}) · n={args.n} × runs={args.runs}")

    graph = build_diagnose_graph()
    rows = []
    for i in range(args.runs):
        print(f"[run {i+1}/{args.runs}] ...", end=" ", flush=True)
        try:
            r = _run_one(graph, student, args.n, args.mode)
            rows.append(r)
            print(
                f"path={r['n_path']} targeting={r['objective']['targeting']} "
                f"resource_hit={r['objective']['resource_hit']} "
                f"LLM={r['llm_score']}"
            )
        except Exception as e:
            print(f"FAIL: {e}")

    if not rows:
        print("[ERR] 无成功运行")
        return 2

    agg = _aggregate(rows)
    md = _render_md(rows, agg, args)
    print()
    print(md)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"[OK] 报告已写入 {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
