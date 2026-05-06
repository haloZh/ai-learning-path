from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="个性化学习路径系统", lifespan=lifespan)


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
