import logging
import random
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models, schemas
from .agents import (
    build_diagnose_graph,
    build_evaluate_graph,
    build_optimize_graph,
)
from .database import get_db, init_db

# 让 app.* 的 logger 在 uvicorn 控制台可见(uvicorn 默认只配 uvicorn.* logger)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_WEB_DIR = _PROJECT_ROOT / "web"


def _resolve_dist() -> Path:
    """选择前端构建产物目录。

    优先 ymy/dist(当前活跃前端),回退 frontend/dist(旧版),
    可用环境变量 FRONTEND_DIST 覆盖。单服务部署时由 FastAPI 托管该目录。
    """
    import os
    env = os.getenv("FRONTEND_DIST")
    if env:
        return Path(env)
    ymy = _PROJECT_ROOT / "ymy" / "dist"
    if ymy.exists():
        return ymy
    return _PROJECT_ROOT / "frontend" / "dist"


_DIST_DIR = _resolve_dist()

_DIAGNOSE_GRAPH = build_diagnose_graph()
_EVALUATE_GRAPH = build_evaluate_graph()
_OPTIMIZE_GRAPH = build_optimize_graph()


def _warmup_rag_sync() -> None:
    """同步预热 RAG 模型 + Chroma collection,在 startup 后台线程调用。"""
    import time as _t
    from .agents.rag import get_rag
    t0 = _t.perf_counter()
    try:
        rag = get_rag()
        _ = rag.model
        _ = rag.collection
        rag.model.encode(["warmup"], show_progress_bar=False)
        logger.info("⏱ RAG 预热完成 %.0f ms", (_t.perf_counter() - t0) * 1000)
    except Exception as e:
        logger.warning("RAG 预热失败(将懒加载兜底): %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    import asyncio
    asyncio.get_event_loop().run_in_executor(None, _warmup_rag_sync)
    yield


app = FastAPI(title="个性化学习路径系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_SPA_ROUTES = {"/profile", "/diagnose", "/path", "/learn", "/assess"}


@app.middleware("http")
async def _spa_or_api(request, call_next):
    """SPA fallback + 慢请求 log。

    路径兼容: /profile /diagnose /path 既是 SPA 路由也是 API。
    判定: GET 请求 + 路径在 SPA 白名单 + Accept 含 text/html → 返回 SPA index.html;
    其他场景透传给后续路由。
    """
    import time as _t
    method = request.method
    path = request.url.path

    # SPA 拦截:浏览器导航/刷新前端路由时
    if method == "GET":
        accept = request.headers.get("accept", "")
        first_seg = "/" + (path.lstrip("/").split("/", 1)[0] if path != "/" else "")
        if first_seg in _SPA_ROUTES and "text/html" in accept:
            return _spa_index()

    t0 = _t.perf_counter()
    response = await call_next(request)
    elapsed = (_t.perf_counter() - t0) * 1000
    if elapsed > 1000:
        logger.info("⏱ %s %s -> %d %.0f ms",
                    method, path, response.status_code, elapsed)
    return response

if _DIST_DIR.exists():
    # 生产路径:Vue 构建产物。/assets 由 Vite 生成,需直接 serve;SPA 路由由
    # 末尾 catch-all 兜底,因此 StaticFiles 不挂 / 根目录。
    app.mount(
        "/assets",
        StaticFiles(directory=str(_DIST_DIR / "assets")),
        name="assets",
    )

if _WEB_DIR.exists():
    # 旧版 demo.html 仍保留,可通过 /static/demo.html 访问
    app.mount("/static", StaticFiles(directory=str(_WEB_DIR)), name="static")


def _spa_index() -> FileResponse:
    """优先返回 Vue 构建产物 dist/index.html;否则降级到 web/demo.html。"""
    if _DIST_DIR.exists():
        idx = _DIST_DIR / "index.html"
        if idx.exists():
            return FileResponse(idx)
    demo = _WEB_DIR / "demo.html"
    if demo.exists():
        return FileResponse(demo)
    raise HTTPException(status_code=404, detail="frontend not built; run `npm run build`")


@app.get("/", include_in_schema=False)
def index():
    return _spa_index()


@app.get("/favicon.svg", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """单服务部署时托管前端图标(dist 根目录,不在 /assets 下)。"""
    for name in ("favicon.svg", "favicon.ico"):
        f = _DIST_DIR / name
        if f.exists():
            return FileResponse(f)
    raise HTTPException(status_code=404, detail="no favicon")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/profile", response_model=schemas.StudentOut, status_code=201)
def create_profile(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    student = models.Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@app.get("/profile/{student_id}", response_model=schemas.StudentOut)
def get_profile(student_id: int, db: Session = Depends(get_db)):
    student = db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="student not found")
    return student


@app.get("/profile", response_model=list[schemas.StudentOut])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(models.Student).order_by(models.Student.id.desc()).all()


@app.get("/concepts", response_model=list[schemas.ConceptOut])
def list_concepts(subject: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Concept)
    if subject:
        q = q.filter(models.Concept.subject == subject)
    return q.order_by(models.Concept.code).all()


@app.get("/questions/sample", response_model=list[schemas.QuestionOut])
def sample_questions(n: int = 5, db: Session = Depends(get_db)):
    """随机抽 n 道题,每个 concept_code 至多 1 道,保证多样性。"""
    n = max(1, min(n, 30))
    all_q = db.query(models.Question).all()
    random.shuffle(all_q)
    seen: set[str] = set()
    out: list[models.Question] = []
    for q in all_q:
        if q.concept_code in seen:
            continue
        seen.add(q.concept_code)
        out.append(q)
        if len(out) >= n:
            break
    return out


def _upsert_learning_path(
    db: Session,
    student_id: int,
    path: list[dict],
    reasoning: list[str],
    is_mock: bool,
) -> None:
    row = db.query(models.LearningPath).filter_by(student_id=student_id).one_or_none()
    if row is None:
        row = models.LearningPath(student_id=student_id)
        db.add(row)
    row.path = path
    row.reasoning = reasoning
    row.is_mock = is_mock


def _run_evaluate_async(
    student_id: int,
    profile: dict,
    mastery: dict,
    path: list[dict],
    resource_pool: dict,
) -> None:
    """后台异步跑评价 Agent,完成后写入 plan_evaluations。

    用独立 DB 会话(后台任务在响应返回后执行,原请求的 db 已关闭)。
    失败只记日志,不影响主流程——前端轮询拿不到评分时显示"计算中"即可。
    """
    if not path:
        return
    try:
        result = _EVALUATE_GRAPH.invoke(
            {
                "student_profile": profile,
                "mastery": mastery,
                "path": path,
                "resource_pool": resource_pool,
                "reasoning": [],
                "used_mock": False,
            }
        )
        evaluation = result.get("evaluation") or None
        if not evaluation:
            return
        used_mock = result.get("used_mock", False)
        from .database import SessionLocal
        with SessionLocal() as db:
            db.add(
                models.PlanEvaluation(
                    student_id=student_id,
                    score=evaluation["score"],
                    scores=evaluation.get("scores", {}),
                    strengths=evaluation.get("strengths"),
                    improvements=evaluation.get("improvements"),
                    summary=evaluation.get("summary"),
                    is_mock=used_mock,
                )
            )
            db.commit()
        logger.info("⏱ 后台评价完成 student=%s score=%s", student_id, evaluation["score"])
    except Exception as e:
        logger.warning("后台评价失败 student=%s: %s", student_id, e)


@app.post("/diagnose", response_model=schemas.DiagnoseResponse)
def diagnose(
    payload: schemas.DiagnoseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    student = db.get(models.Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="student not found")

    profile = {
        "subject": student.subject,
        "cognitive_level": student.cognitive_level,
        "learning_style": student.learning_style,
        "learning_goal": student.learning_goal,
        "available_minutes_per_day": student.available_minutes_per_day,
    }

    try:
        # 诊断主链:只跑 diagnose -> plan,尽快返回路径
        result = _DIAGNOSE_GRAPH.invoke(
            {
                "student_id": payload.student_id,
                "student_profile": profile,
                "answers": [a.model_dump() for a in payload.answers],
                "reasoning": [],
                "used_mock": False,
            }
        )
        mastery = result.get("mastery", {})
        path = result.get("path", [])
        reasoning = result.get("reasoning", [])
        used_mock = result.get("used_mock", False)
        resource_pool = result.get("resource_pool", {}) or {}

        db.add(
            models.MasterySnapshot(
                student_id=payload.student_id,
                mastery=mastery,
                reasoning=reasoning,
                is_mock=used_mock,
            )
        )
        _upsert_learning_path(db, payload.student_id, path, reasoning, used_mock)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("diagnose failed: %s", e)
        raise HTTPException(status_code=500, detail="diagnose 内部错误,请稍后重试") from e

    # 评价 Agent 放后台异步执行,不阻塞本次响应;前端轮询 GET /path 拿评分
    background_tasks.add_task(
        _run_evaluate_async,
        payload.student_id, profile, mastery, path, resource_pool,
    )

    return schemas.DiagnoseResponse(
        student_id=payload.student_id,
        mastery=mastery,
        path=path,
        reasoning=reasoning,
        evaluation=None,  # 评分异步生成,前端轮询 GET /path 获取
        mock=used_mock,
    )


def _latest_evaluation(db: Session, student_id: int) -> schemas.EvaluationOut | None:
    """取该学生最近一次的 plan_evaluations 行,序列化为 EvaluationOut。"""
    row = (
        db.query(models.PlanEvaluation)
        .filter_by(student_id=student_id)
        .order_by(models.PlanEvaluation.created_at.desc())
        .first()
    )
    if row is None:
        return None
    return schemas.EvaluationOut(
        score=row.score,
        scores=schemas.EvaluationScores(**(row.scores or {})),
        strengths=row.strengths,
        improvements=row.improvements,
        summary=row.summary,
        mock=row.is_mock,
    )


@app.get("/path/{student_id}", response_model=schemas.LearningPathResponse)
def get_path(student_id: int, db: Session = Depends(get_db)):
    row = db.query(models.LearningPath).filter_by(student_id=student_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="no path; run /diagnose first")
    return schemas.LearningPathResponse(
        student_id=student_id,
        path=row.path or [],
        reasoning=row.reasoning or [],
        evaluation=_latest_evaluation(db, student_id),
        mock=row.is_mock,
    )


@app.post("/interaction", response_model=schemas.InteractionResponse)
def post_interaction(event: schemas.InteractionEvent, db: Session = Depends(get_db)):
    row = db.query(models.LearningPath).filter_by(student_id=event.student_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="no path; run /diagnose first")

    try:
        db.add(
            models.Interaction(
                student_id=event.student_id,
                event=event.event,
                concept_code=event.concept_id,
                detail=event.detail,
            )
        )
        result = _OPTIMIZE_GRAPH.invoke(
            {
                "student_id": event.student_id,
                "path": row.path or [],
                "interaction": event.model_dump(),
                "reasoning": [],
                "used_mock": False,
            }
        )
        path = result.get("path", [])
        reasoning = result.get("reasoning", [])
        used_mock = result.get("used_mock", False)

        _upsert_learning_path(db, event.student_id, path, reasoning, used_mock)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("interaction failed: %s", e)
        raise HTTPException(status_code=500, detail="interaction 内部错误,请稍后重试") from e

    return schemas.InteractionResponse(
        student_id=event.student_id,
        path=path,
        reasoning=reasoning,
        # interaction 不重跑 evaluate,沿用最近一次诊断的评价
        evaluation=_latest_evaluation(db, event.student_id),
        mock=used_mock,
    )


# 路径兼容性说明:
#   /profile /diagnose /path 既是后端 API 也是前端 SPA 路由(history 模式)。
#   两者通过 Accept header 区分:
#   - 浏览器导航/刷新: Accept 含 'text/html' → 返回 SPA index.html
#   - axios/fetch JSON: Accept 是 'application/json' / '*/*' → 走业务 API
#   这个 middleware 必须在路由匹配 *之前* 拦截,所以放在 startup 后用
#   @app.middleware('http') 注册。
