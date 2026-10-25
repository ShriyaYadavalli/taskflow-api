from fastapi import Depends, FastAPI, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.schemas import TaskCreate, TaskResponse

# Create tables that don't exist yet.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskFlow API")


@app.get("/")
def root():
    return {"message": "Welcome to TaskFlow API!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    statement = select(models.Task).order_by(models.Task.id)
    tasks = db.scalars(statement).all()
    return tasks


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
):
    task = models.Task(**task_data.model_dump())

    db.add(task)
    db.commit()
    db.refresh(task)

    return task
