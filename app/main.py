from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .agents import build_diagnose_graph, build_optimize_graph
from .database import get_db, init_db

_DIAGNOSE_GRAPH = build_diagnose_graph()
_OPTIMIZE_GRAPH = build_optimize_graph()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="个性化学习路径系统", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/diagnose", response_model=schemas.DiagnoseResponse)
def diagnose(payload: schemas.DiagnoseRequest, db: Session = Depends(get_db)):
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

    return schemas.DiagnoseResponse(
        student_id=payload.student_id,
        mastery=mastery,
        path=path,
        reasoning=reasoning,
        mock=used_mock,
    )


@app.get("/path/{student_id}", response_model=schemas.LearningPathResponse)
def get_path(student_id: int, db: Session = Depends(get_db)):
    row = db.query(models.LearningPath).filter_by(student_id=student_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="no path; run /diagnose first")
    return schemas.LearningPathResponse(
        student_id=student_id,
        path=row.path or [],
        mock=row.is_mock,
    )


@app.post("/interaction", response_model=schemas.InteractionResponse)
def post_interaction(event: schemas.InteractionEvent, db: Session = Depends(get_db)):
    row = db.query(models.LearningPath).filter_by(student_id=event.student_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="no path; run /diagnose first")

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

    return schemas.InteractionResponse(
        student_id=event.student_id,
        path=path,
        reasoning=reasoning,
        mock=used_mock,
    )
