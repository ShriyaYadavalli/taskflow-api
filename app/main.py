from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.schemas import TaskCreate, TaskResponse, TaskUpdate

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
def get_tasks(
    task_status: Literal["pending", "in_progress", "completed"] | None = Query(
        default=None,
        alias="status",
    ),
    priority: Literal["low", "medium", "high"] | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    statement = select(models.Task)

    if task_status is not None:
        statement = statement.where(models.Task.status == task_status)

    if priority is not None:
        statement = statement.where(models.Task.priority == priority)

    statement = (
        statement
        .order_by(models.Task.id)
        .offset(offset)
        .limit(limit)
    )

    tasks = db.scalars(statement).all()
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(models.Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
):
    task = db.get(models.Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    updates = task_data.model_dump(exclude_unset=True)

    if any(
        value is None and field != "description"
        for field, value in updates.items()
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only description may be set to null",
        )

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = db.get(models.Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    db.delete(task)
    db.commit()

    return {"message": f"Task {task_id} deleted successfully"}


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
