from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .agents import build_diagnose_graph, build_optimize_graph
from .database import get_db, init_db

_DIAGNOSE_GRAPH = build_diagnose_graph()
_OPTIMIZE_GRAPH = build_optimize_graph()
_PATH_CACHE: dict[int, list[dict]] = {}


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


@app.post("/diagnose", response_model=schemas.DiagnoseResponse)
def diagnose(payload: schemas.DiagnoseRequest, db: Session = Depends(get_db)):
    if not db.get(models.Student, payload.student_id):
        raise HTTPException(status_code=404, detail="student not found")

    result = _DIAGNOSE_GRAPH.invoke(
        {
            "student_id": payload.student_id,
            "answers": [a.model_dump() for a in payload.answers],
            "reasoning": [],
        }
    )
    _PATH_CACHE[payload.student_id] = result.get("path", [])
    return schemas.DiagnoseResponse(
        student_id=payload.student_id,
        mastery=result.get("mastery", {}),
        path=result.get("path", []),
        reasoning=result.get("reasoning", []),
    )


@app.get("/path/{student_id}", response_model=schemas.LearningPathResponse)
def get_path(student_id: int):
    if student_id not in _PATH_CACHE:
        raise HTTPException(status_code=404, detail="no path; run /diagnose first")
    return schemas.LearningPathResponse(
        student_id=student_id,
        path=_PATH_CACHE[student_id],
    )


@app.post("/interaction", response_model=schemas.InteractionResponse)
def post_interaction(event: schemas.InteractionEvent):
    if event.student_id not in _PATH_CACHE:
        raise HTTPException(status_code=404, detail="no path; run /diagnose first")
    result = _OPTIMIZE_GRAPH.invoke(
        {
            "student_id": event.student_id,
            "path": _PATH_CACHE[event.student_id],
            "interaction": event.model_dump(),
            "reasoning": [],
        }
    )
    _PATH_CACHE[event.student_id] = result.get("path", [])
    return schemas.InteractionResponse(
        student_id=event.student_id,
        path=result.get("path", []),
        reasoning=result.get("reasoning", []),
    )
