"""修复题库 LaTeX 的 JSON 转义损坏。

根因:入库时 choices 等字段的 JSON 字符串里,LaTeX 反斜杠转义不一致——
\\displaystyle 正确(双反斜杠),但 \frac 只有单反斜杠,导致 json.loads
按 JSON 标准把 \f 解析成换页符(form feed),\frac 变 ↑rac 乱码。

修复:对每条记录,先把数据库里存的 JSON 原文中"非法的单反斜杠转义"
补成合法的双反斜杠,再确认 json.loads 能正确还原。

合法的 JSON 转义只有那几个(引号/反斜杠/斜杠/bfnrt/u 开头的 unicode)。
LaTeX 命令如 frac/times/beta 等反斜杠后跟字母,在 JSON 里必须双反斜杠。
本脚本把所有非法的单反斜杠转义补成双反斜杠。

用法:
    .venv/Scripts/python.exe -m scripts.fix_latex_escape          # 预览(dry-run)
    .venv/Scripts/python.exe -m scripts.fix_latex_escape --apply  # 实际修复
"""
import json
import re
import sqlite3
import sys

# JSON 合法转义的后续字符(这些 \x 是合法的,不动)
_VALID_JSON_ESC = set('"\\/bfnrtu')


def fix_json_text(raw: str) -> str:
    """把 JSON 原文里非法的单反斜杠转义补成双反斜杠。

    关键:LaTeX 命令 frac/binom/tan 等以 f/b/t 开头,前面的反斜杠
    被误当成了 JSON 控制转义。本题库内容是数学公式,不含真正的控制字符,
    所以一律视为 LaTeX,反斜杠后跟字符一律补成双反斜杠(已双的不重复加)。
    """
    out = []
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == "\\" and i + 1 < n:
            nxt = raw[i + 1]
            if nxt == "\\":
                # 已是 \\,原样保留两个字符
                out.append("\\\\")
                i += 2
                continue
            if nxt == "u":
                # \uXXXX 合法,保留
                out.append(raw[i : i + 2])
                i += 2
                continue
            if nxt in '"/':
                # \" \/ 合法 JSON 转义,保留
                out.append(raw[i : i + 2])
                i += 2
                continue
            if nxt in "bfnrt":
                # 这几个虽是合法 JSON 转义,但在本题库里几乎都是 LaTeX 命令
                # (\frac \binom \times \nu \root...),补成 \\ 让其还原为字面反斜杠
                out.append("\\\\")
                out.append(nxt)
                i += 2
                continue
            # \ + 其他字符(字母如 \d \s,符号等):补成 \\
            out.append("\\\\")
            out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def main():
    apply = "--apply" in sys.argv
    c = sqlite3.connect("data/app.db")
    rows = c.execute("select id, stem, choices, explanation from questions").fetchall()

    fixed_count = 0
    samples = []
    for id_, stem, choices, expl in rows:
        updates = {}
        for col, raw in (("stem", stem), ("choices", choices), ("explanation", expl)):
            if not raw:
                continue
            # 先看当前 json.loads 后是否含控制字符(损坏标志)
            try:
                parsed = json.loads(raw) if col == "choices" else raw
            except json.JSONDecodeError:
                parsed = raw
            blob = json.dumps(parsed, ensure_ascii=False) if isinstance(parsed, (dict, list)) else str(parsed)
            has_ctrl = any(ord(x) in (8, 9, 11, 12, 13) for x in (
                "".join(parsed.values()) if isinstance(parsed, dict) else str(parsed)
            ))
            if not has_ctrl:
                continue
            # 修复:重新解析原始 JSON 前先补转义
            fixed = fix_json_text(raw)
            # 验证修复后能正常解析且无控制字符
            try:
                p2 = json.loads(fixed) if col == "choices" else fixed
                check = "".join(p2.values()) if isinstance(p2, dict) else str(p2)
                if any(ord(x) in (8, 9, 11, 12, 13) for x in check):
                    continue  # 还有问题,跳过
            except json.JSONDecodeError:
                continue
            updates[col] = fixed
            if len(samples) < 5:
                samples.append((id_, col, raw[:80], fixed[:80]))
        if updates:
            fixed_count += 1
            if apply:
                set_clause = ", ".join(f"{k}=?" for k in updates)
                c.execute(
                    f"update questions set {set_clause} where id=?",
                    (*updates.values(), id_),
                )

    print(f"{'已修复' if apply else '待修复(dry-run)'}题目数: {fixed_count}")
    print("\n样例(原文 -> 修复后):")
    for id_, col, before, after in samples:
        print(f"  id={id_} {col}")
        print(f"    前: {before}")
        print(f"    后: {after}")

    if apply:
        c.commit()
        print("\n[OK] 已写入数据库")
    else:
        print("\n预览模式,加 --apply 实际修复")


if __name__ == "__main__":
    main()
