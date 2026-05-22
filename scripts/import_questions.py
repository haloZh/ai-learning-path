"""把人工录入的题库 xlsx 导入 questions 表。

用法:
    .venv/bin/python -m scripts.import_questions <xlsx 路径> [sheet 名]

行为:
- 默认读 "录入表(同学填这里)" sheet,可通过参数覆盖
- 第 1 行为字段名(英文),第 2 行为中文说明,从第 3 行开始为题目数据
- (category, knowledge_point) -> concept_code 通过 concepts.aliases 反查
- 同 stem+source+year 视作重复,跳过(脚本可重复跑)
- 失败行集中报告,不影响成功行入库
- LaTeX 原文照存,不做任何转义
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import openpyxl

from app.database import SessionLocal, init_db
from app.models import Concept, Question

DEFAULT_SHEET = "录入表(同学填这里)"
ALT_SHEET = "录入表(同学填这里)"


def _norm(value) -> str:
    return str(value).strip() if value is not None else ""


def _to_int(value, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_choices(value) -> dict | list:
    """options 字段:可能是 dict / JSON 字符串 / 空。"""
    if value in (None, ""):
        return {}
    if isinstance(value, (dict, list)):
        return value
    text = str(value).strip()
    if not text:
        return {}
    return json.loads(text)


def _parse_tags(value) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(t).strip() for t in value if str(t).strip()]
    return [t.strip() for t in str(value).split(",") if t.strip()]


def _build_alias_map(db) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for c in db.query(Concept).all():
        for a in c.aliases or []:
            key = (_norm(a.get("category")), _norm(a.get("knowledge_point")))
            if all(key):
                out[key] = c.code
    return out


def _pick_sheet(wb: openpyxl.Workbook, sheet_name: str | None):
    if sheet_name and sheet_name in wb.sheetnames:
        return wb[sheet_name]
    # 默认行为: 优先匹配名称里有 "录入" 的 sheet
    for name in wb.sheetnames:
        if "录入" in name:
            return wb[name]
    return wb[wb.sheetnames[0]]


def import_xlsx(xlsx_path: Path, sheet_name: str | None = None) -> dict:
    init_db()
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = _pick_sheet(wb, sheet_name)

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 3:
        return {"success": 0, "skipped": 0, "failed": [], "note": "sheet 行数 < 3,无可导入数据"}

    headers = [_norm(h) for h in rows[0]]
    header_idx = {h: i for i, h in enumerate(headers) if h}

    required = {"category", "knowledge_point", "content", "correct_answer"}
    missing = required - set(header_idx)
    if missing:
        raise ValueError(f"xlsx 缺少必需列: {sorted(missing)},请用最新模板录入")

    success = 0
    skipped = 0
    failed: list[dict] = []

    with SessionLocal() as db:
        alias_map = _build_alias_map(db)

        for row_num, row in enumerate(rows[2:], start=3):  # 第 3 行起为数据
            if not any(row):
                continue

            data = {h: row[i] for h, i in header_idx.items() if i < len(row)}
            category = _norm(data.get("category"))
            knowledge_point = _norm(data.get("knowledge_point"))
            stem = _norm(data.get("content"))

            if not category or not knowledge_point:
                failed.append({"row": row_num, "reason": "category 或 knowledge_point 为空"})
                continue
            if not stem:
                failed.append({"row": row_num, "reason": "content 为空"})
                continue

            concept_code = alias_map.get((category, knowledge_point))
            if not concept_code:
                failed.append({
                    "row": row_num,
                    "reason": f"未找到匹配的 concept_code: ({category} - {knowledge_point}),"
                              f"请对照 docs/概念清单.md 修正",
                })
                continue

            try:
                choices = _parse_choices(data.get("options"))
            except json.JSONDecodeError:
                failed.append({"row": row_num, "reason": "options JSON 解析失败"})
                continue

            source = _norm(data.get("source")) or None
            year = _to_int(data.get("year"))

            existing = (
                db.query(Question)
                .filter(
                    Question.stem == stem,
                    Question.source == source,
                    Question.year == year,
                )
                .first()
            )
            if existing:
                skipped += 1
                continue

            db.add(
                Question(
                    concept_code=concept_code,
                    question_type=_norm(data.get("question_type")) or "single_choice",
                    stem=stem,
                    choices=choices,
                    answer=_norm(data.get("correct_answer")),
                    difficulty=_to_int(data.get("difficulty"), 1) or 1,
                    score=_to_int(data.get("score"), 3) or 3,
                    explanation=_norm(data.get("explanation")) or None,
                    source=source,
                    year=year,
                    tags=_parse_tags(data.get("tags")),
                )
            )
            success += 1

        db.commit()

    return {"success": success, "skipped": skipped, "failed": failed}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法: python -m scripts.import_questions <xlsx 路径> [sheet 名]", file=sys.stderr)
        return 1

    xlsx_path = Path(argv[1]).expanduser()
    if not xlsx_path.exists():
        print(f"[ERR] 文件不存在: {xlsx_path}", file=sys.stderr)
        return 1

    sheet_name = argv[2] if len(argv) > 2 else None

    result = import_xlsx(xlsx_path, sheet_name)
    print(f"[OK] 成功 {result['success']} 条, 跳过(重复) {result['skipped']} 条, "
          f"失败 {len(result['failed'])} 条")
    if result["failed"]:
        print("--- 失败明细 ---")
        for f in result["failed"]:
            print(f"  行 {f['row']}: {f['reason']}")
    return 0 if not result["failed"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
