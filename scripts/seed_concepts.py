"""管综·数学基础 概念种子。以 code 为唯一键 upsert 到 concepts 表。

用法:
    .venv/bin/python -m scripts.seed_concepts
"""

from app.database import SessionLocal, init_db
from app.models import Concept

SUBJECT = "管综数学"

CONCEPTS: list[dict] = [
    # ===== 算术(11) =====
    {"code": "算术-整数运算", "name": "整数运算", "prerequisite_codes": [],
     "description": "加减乘除、除法分配律、运算优先级"},
    {"code": "算术-奇偶质合数", "name": "奇偶与质合数", "prerequisite_codes": ["算术-整数运算"],
     "description": "奇偶判定、质数合数、整除性、最大公约/最小公倍"},
    {"code": "算术-绝对值", "name": "绝对值", "prerequisite_codes": ["算术-整数运算"],
     "description": "绝对值定义、几何意义、绝对值不等式入门"},
    {"code": "算术-分数运算", "name": "分数运算", "prerequisite_codes": ["算术-整数运算"],
     "description": "通分约分、繁分式化简、分数四则运算"},
    {"code": "算术-小数与百分数", "name": "小数与百分数", "prerequisite_codes": ["算术-分数运算"],
     "description": "小数与分数互化、百分数应用"},
    {"code": "算术-比例", "name": "比与比例", "prerequisite_codes": ["算术-分数运算"],
     "description": "比的基本性质、连比、正反比例"},
    {"code": "算术-平均数", "name": "平均值与加权", "prerequisite_codes": ["算术-分数运算"],
     "description": "算术平均、加权平均、混合应用"},
    {"code": "算术-应用题-行程", "name": "行程问题", "prerequisite_codes": ["算术-比例"],
     "description": "相遇、追及、流水行船、火车过桥"},
    {"code": "算术-应用题-工程", "name": "工程问题", "prerequisite_codes": ["算术-比例"],
     "description": "效率叠加、合作完工、轮换工作"},
    {"code": "算术-应用题-浓度", "name": "浓度问题",
     "prerequisite_codes": ["算术-比例", "算术-小数与百分数"],
     "description": "溶质守恒、稀释/浓缩、十字交叉法"},
    {"code": "算术-应用题-利润", "name": "利润问题", "prerequisite_codes": ["算术-小数与百分数"],
     "description": "成本-定价-售价、折扣、利润率"},

    # ===== 代数(11) =====
    {"code": "代数-整式运算", "name": "整式运算", "prerequisite_codes": ["算术-整数运算"],
     "description": "合并同类项、乘法公式、因式分解"},
    {"code": "代数-分式运算", "name": "分式化简",
     "prerequisite_codes": ["代数-整式运算", "算术-分数运算"],
     "description": "分式通分、约分、繁分式化简"},
    {"code": "代数-一元一次方程", "name": "一元一次方程", "prerequisite_codes": ["代数-整式运算"],
     "description": "解法、应用题建模"},
    {"code": "代数-一元二次方程", "name": "一元二次方程基础",
     "prerequisite_codes": ["代数-一元一次方程"],
     "description": "求根公式、配方法、十字相乘"},
    {"code": "代数-一元二次方程-判别式", "name": "判别式与根的分布",
     "prerequisite_codes": ["代数-一元二次方程"],
     "description": "Δ 与实根关系、根的正负分布判断"},
    {"code": "代数-一元二次方程-韦达定理", "name": "韦达定理",
     "prerequisite_codes": ["代数-一元二次方程"],
     "description": "根与系数关系、对称式求值"},
    {"code": "代数-不等式", "name": "不等式", "prerequisite_codes": ["代数-一元一次方程"],
     "description": "一元一次/二次不等式、绝对值不等式"},
    {"code": "代数-数列-等差", "name": "等差数列", "prerequisite_codes": ["代数-整式运算"],
     "description": "通项公式、求和公式、性质"},
    {"code": "代数-数列-等比", "name": "等比数列", "prerequisite_codes": ["代数-数列-等差"],
     "description": "通项公式、求和公式、错位相减入门"},
    {"code": "代数-函数与图象", "name": "函数与图象",
     "prerequisite_codes": ["代数-一元二次方程"],
     "description": "一次/二次函数图象、最值、对称性"},
    {"code": "代数-指数与对数", "name": "指数与对数",
     "prerequisite_codes": ["代数-整式运算"],
     "description": "指数运算法则、对数定义与换底公式(管综不深考)"},

    # ===== 几何(7) =====
    {"code": "几何-平面几何-直线与角", "name": "直线与角",
     "prerequisite_codes": ["算术-整数运算"],
     "description": "平行线性质、角度和差、对顶/邻补"},
    {"code": "几何-平面几何-三角形", "name": "三角形",
     "prerequisite_codes": ["几何-平面几何-直线与角"],
     "description": "全等/相似、勾股定理、特殊三角形"},
    {"code": "几何-平面几何-四边形", "name": "四边形",
     "prerequisite_codes": ["几何-平面几何-三角形"],
     "description": "平行四边形、矩形、菱形、梯形"},
    {"code": "几何-平面几何-圆", "name": "圆",
     "prerequisite_codes": ["几何-平面几何-三角形"],
     "description": "圆心角圆周角、切线、弦长公式"},
    {"code": "几何-解析几何-直线方程", "name": "直线方程",
     "prerequisite_codes": ["代数-一元一次方程", "几何-平面几何-直线与角"],
     "description": "斜截式/点斜式/一般式、平行垂直判定"},
    {"code": "几何-解析几何-圆方程", "name": "圆方程",
     "prerequisite_codes": ["代数-一元二次方程", "几何-平面几何-圆"],
     "description": "标准方程、一般方程、点与圆/直线与圆位置关系"},
    {"code": "几何-空间几何体", "name": "立体几何",
     "prerequisite_codes": ["几何-平面几何-三角形"],
     "description": "正方体、长方体、圆柱圆锥球的体积与表面积"},

    # ===== 数据分析(4) =====
    {"code": "数据分析-排列", "name": "排列",
     "prerequisite_codes": ["算术-整数运算"],
     "description": "排列数公式、有序选取"},
    {"code": "数据分析-组合", "name": "组合",
     "prerequisite_codes": ["数据分析-排列"],
     "description": "组合数公式、无序选取、组合恒等式"},
    {"code": "数据分析-古典概率", "name": "古典概率",
     "prerequisite_codes": ["数据分析-组合", "算术-分数运算"],
     "description": "古典概型、互斥/独立事件、条件概率"},
    {"code": "数据分析-数据描述", "name": "数据描述",
     "prerequisite_codes": ["算术-平均数"],
     "description": "众数中位数、方差标准差(管综侧重描述统计)"},
]


def seed() -> tuple[int, int]:
    init_db()
    inserted = 0
    updated = 0
    with SessionLocal() as db:
        for item in CONCEPTS:
            row = db.query(Concept).filter_by(code=item["code"]).one_or_none()
            if row is None:
                db.add(
                    Concept(
                        code=item["code"],
                        name=item["name"],
                        subject=SUBJECT,
                        prerequisite_codes=item["prerequisite_codes"],
                        description=item.get("description"),
                    )
                )
                inserted += 1
            else:
                row.name = item["name"]
                row.subject = SUBJECT
                row.prerequisite_codes = item["prerequisite_codes"]
                row.description = item.get("description")
                updated += 1
        db.commit()
    return inserted, updated


def main() -> None:
    ins, upd = seed()
    print(f"[OK] concepts: 插入 {ins} 条, 更新 {upd} 条, 总计 {len(CONCEPTS)} 个知识点")


if __name__ == "__main__":
    main()
