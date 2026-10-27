from typing import Annotated

from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from tasks.models import TaskModel
from tasks.schemas import BaseTaskSchema

DB_SESSION = Depends(get_db)

router = APIRouter(tags=["tasks"], prefix="/tasks")


TaskId = Annotated[int, Path(gt=0)]


def get_task_or_404(db: Session, task_id: int) -> TaskModel:
    task = db.get(TaskModel, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# Get all tasks or search tasks by title
@router.get("/")
def get_tasks(
    q: Annotated[str | None, Query(alias="search", max_length=30)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Session = DB_SESSION,
):

    query = select(TaskModel).order_by(TaskModel.id).offset(skip).limit(limit)

    if q:
        query = query.where(TaskModel.title.icontains(q, autoescape=True))
    return db.scalars(query).all()


# Get a task by its ID
@router.get("/{task_id}")
def get_task(task_id: TaskId, db: Session = DB_SESSION):
    return get_task_or_404(db, task_id)


# Create a new task
@router.post("/", status_code=201)
def create_task(task: BaseTaskSchema, db: Session = DB_SESSION):
    new_task = TaskModel(**task.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {
        "message": "Task created successfully",
        "new_task": {
            "id": new_task.id,
            "title": new_task.title,
            "description": new_task.description,
            "is_completed": new_task.is_completed,
        },
    }


# Update a task by its ID
@router.put("/{task_id}")
def update_task(
    task_id: Annotated[int, Path(gt=0)],
    updated_task: Annotated[BaseTaskSchema, ...],
    db: Session = DB_SESSION,
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = updated_task.title
    task.description = updated_task.description
    task.is_completed = updated_task.is_completed
    task.user_id = updated_task.user_id

    db.commit()
    db.refresh(task)

    return {
        "message": "Task updated successfully",
        "updated_task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "is_completed": task.is_completed,
            "user_id": task.user_id,
        },
    }


# Delete a task by its ID
@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: TaskId,
    db: Session = DB_SESSION,
):

    task = get_task_or_404(db, task_id)
    db.delete(task)
    db.commit()
