from typing import Literal
import pika
from pydantic import BaseModel, Field

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.queue import publish_task_message
from app.database import get_db
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)



app = FastAPI(title="TaskFlow API")
class JobRequest(BaseModel):
    job_type: str = Field(min_length=1, max_length=100)
    payload: dict[str, object] = Field(default_factory=dict)


@app.get("/")
def root():
    return {"message": "Welcome to TaskFlow API!"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
def create_job(job_data: JobRequest):
    message = job_data.model_dump()

    try:
        publish_task_message(message)
    except (pika.exceptions.AMQPError, OSError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job queue is currently unavailable",
        )

    return {
        "status": "queued",
        "job": message,
    }


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

    if updates.get("project_id") is not None:
        project = db.get(models.Project, updates["project_id"])

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

    if any(
        value is None and field not in {"description", "project_id"}
        for field, value in updates.items()
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only description and project_id may be set to null",
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
    if task_data.project_id is not None:
        project = db.get(models.Project, task_data.project_id)

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
    
    task = models.Task(**task_data.model_dump())

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@app.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    project = models.Project(**project_data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.get("/projects", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    statement = select(models.Project).order_by(models.Project.id)
    return db.scalars(statement).all()


@app.get(
    "/projects/{project_id}/tasks",
    response_model=list[TaskResponse],
)
def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(models.Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    statement = (
        select(models.Task)
        .where(models.Task.project_id == project_id)
        .order_by(models.Task.id)
    )
    return db.scalars(statement).all()
