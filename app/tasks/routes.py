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
@router.get("/", status_code=200)
def get_tasks(
    q: Annotated[str | None, Query(alias="search", max_length=30)] = None,
    db: Session = DB_SESSION,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):

    query = select(TaskModel).order_by(TaskModel.id).offset(skip).limit(limit)

    if q:
        query = query.where(TaskModel.title.icontains(q, autoescape=True))
    return db.scalars(query).all()


# Get a task by it's ID
@router.get("/{task_id}", status_code=200)
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


# Update a task
@router.put("/{task_id}", status_code=200)
def update_task(
    task_id: TaskId,
    updated_task: BaseTaskSchema,
    db: Session = DB_SESSION,
):
    task = get_task_or_404(db, task_id)
    for field, value in updated_task.model_dump().items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)

    return {
        "message": "Task updated successfully",
        "updated_task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "is_completed": task.is_completed,
        },
    }


# Delete a task by it's ID
@router.delete("/{task_id}", status_code=200)
def delete_task(
    task_id: TaskId,
    db: Session = DB_SESSION,
):

    task = get_task_or_404(db, task_id)
    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully", "deleted_task": task}
