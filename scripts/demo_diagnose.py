"""从题库抽真题做诊断 demo,直接走 LangGraph 链路,不依赖 uvicorn / 不写库。

适合答辩演示与 prompt / RAG 调优后的回归对比。

用法:
    .venv/bin/python -m scripts.demo_diagnose
    .venv/bin/python -m scripts.demo_diagnose --n 8 --mode wrong --seed 42
    .venv/bin/python -m scripts.demo_diagnose --student-id 1 --mode mixed

参数:
    --n           抽题数量(默认 5,每题取自不同 concept_code)
    --student-id  模拟学生(默认 1,需已存在于 students 表)
    --mode        wrong|right|mixed,模拟答题正确率(默认 mixed,按难度反向加权)
    --seed        随机种子,固定后可重复演示
"""

from __future__ import annotations

import argparse
import random
import sys

from app.agents import build_diagnose_graph
from app.database import SessionLocal
from app.models import Question, Student


def _sample_questions(db, n: int) -> list[Question]:
    """每个 concept_code 至多抽 1 题,优先覆盖多样性。"""
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
    # mixed: 难度 1 → 80% 正确,难度 5 → 20% 正确
    prob_correct = max(0.2, 1.0 - (q.difficulty or 1) * 0.15)
    return random.random() < prob_correct


def _print_bar(score: float, width: int = 20) -> str:
    filled = int(round(score * width))
    return "█" * filled + "░" * (width - filled)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=5, help="抽题数量(默认 5)")
    parser.add_argument("--student-id", type=int, default=1, help="模拟学生(默认 1)")
    parser.add_argument(
        "--mode", choices=["wrong", "right", "mixed"], default="mixed",
        help="模拟答题模式(默认 mixed,按难度加权)"
    )
    parser.add_argument("--seed", type=int, default=None, help="随机种子(可选)")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    with SessionLocal() as db:
        student = db.get(Student, args.student_id)
        if not student:
            print(f"[ERR] student_id={args.student_id} 不存在,请先 POST /profile 创建")
            return 1

        questions = _sample_questions(db, args.n)
        if not questions:
            print("[ERR] questions 表为空,请先跑 import_questions")
            return 1

        answers = []
        print(f"=== 学生画像 ===")
        print(f"  昵称       : {student.nickname}")
        print(f"  学科       : {student.subject}")
        print(f"  认知层     : {student.cognitive_level}")
        print(f"  学习目标   : {student.learning_goal}")
        print(f"  日均时间   : {student.available_minutes_per_day} min")
        print(f"  学习风格   : {student.learning_style}")

        print(f"\n=== 模拟答卷({len(questions)} 题,mode={args.mode}) ===")
        for i, q in enumerate(questions, 1):
            correct = _fake_answer(q, args.mode)
            seconds = random.randint(20, 200)
            answers.append({
                "question_id": q.id,
                "concept_id": q.concept_code,
                "correct": correct,
                "seconds": seconds,
            })
            mark = "✓" if correct else "✗"
            stem_preview = (q.stem or "").replace("\n", " ")[:40]
            print(f"  Q{i:2d} {mark} [{q.concept_code}] 难度 {q.difficulty}, {seconds}s")
            print(f"        {stem_preview}...")

        profile = {
            "subject": student.subject,
            "cognitive_level": student.cognitive_level,
            "learning_style": student.learning_style,
            "learning_goal": student.learning_goal,
            "available_minutes_per_day": student.available_minutes_per_day,
        }

    print("\n=== 启动诊断链(LLM + RAG,约 5–15s)... ===\n")
    graph = build_diagnose_graph()
    result = graph.invoke({
        "student_id": args.student_id,
        "student_profile": profile,
        "answers": answers,
        "reasoning": [],
        "used_mock": False,
    })

    mastery = result.get("mastery", {})
    print("--- 掌握度评估 ---")
    if mastery:
        max_key_len = max(len(k) for k in mastery)
        for k, v in sorted(mastery.items(), key=lambda kv: kv[1]):
            print(f"  {k:<{max_key_len}}  {v:.2f}  {_print_bar(v)}")
    else:
        print("  (空)")

    print("\n--- 推荐学习路径 ---")
    for i, p in enumerate(result.get("path", []), 1):
        print(f"  {i}. {p['title']}  ({p['estimated_minutes']} min)")
        print(f"     reason: {p['reason']}")

    print("\n--- 推理日志 ---")
    for r in result.get("reasoning", []):
        print(f"  {r}")

    used_mock = result.get("used_mock", False)
    flag = "MOCK 兜底 ⚠️" if used_mock else "LLM ✓"
    print(f"\n--- 链路状态: {flag} ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
