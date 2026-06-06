"""诊断题库中 LaTeX 转义损坏情况。

根因:入库时 choices/stem 的 JSON 里 LaTeX 反斜杠未正确转义,
\frac 存成 \f(form feed)等控制字符。本脚本只读、统计,不修改。
"""
import sqlite3

# 会被 json/字符串误吞的控制字符 -> 它本应是的 LaTeX 命令首字母
CTRL = {
    "\x08": "b",   # \b -> \binom 等
    "\x09": "t",   # \t -> \times \tan \theta 等
    "\x0c": "f",   # \f -> \frac 等
    "\x0b": "v",   # \v
    "\r": "r",     # \r
}


def main():
    c = sqlite3.connect("data/app.db")
    rows = c.execute("select id, stem, choices, explanation from questions").fetchall()
    bad = []
    for id_, stem, choices, expl in rows:
        blob = (stem or "") + "\x01" + (choices or "") + "\x01" + (expl or "")
        hits = {hex(ord(ch)): ch for ch in blob if ch in CTRL}
        if hits:
            bad.append((id_, list(hits.keys())))
    print(f"受损题目数: {len(bad)} / {len(rows)}")
    for id_, hits in bad[:20]:
        print(f"  id={id_}  控制字符={hits}")
    # 打印一条样例
    if bad:
        sample_id = bad[0][0]
        row = c.execute(
            "select choices from questions where id=?", (sample_id,)
        ).fetchone()
        print(f"\n样例 id={sample_id} choices 字符:")
        print([hex(ord(x)) if ord(x) < 32 else x for x in row[0]][:40])


if __name__ == "__main__":
    main()
