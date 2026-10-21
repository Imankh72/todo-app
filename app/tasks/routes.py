from typing import Annotated

from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from tasks.models import TaskModel
from tasks.schemas import BaseTaskSchema

DB_SESSION = Depends(get_db)

router = APIRouter(tags=["tasks"], prefix="/tasks")


# Get all tasks or search tasks by title
@router.get("/", status_code=200)
async def get_tasks(
    q: Annotated[str | None, Query(alias="search", max_length=30)] = None,
    db: Session = DB_SESSION,
):

    query = db.query(TaskModel)

    if q:
        query = query.filter(TaskModel.title.ilike(f"%{q}%"))

    tasks = query.all()

    return tasks


# Get a task by it's ID
@router.get("/{task_id}", status_code=200)
async def get_task(task_id: Annotated[int, Path(gt=0)], db: Session = DB_SESSION):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# Create a new task
@router.post("/", status_code=201)
async def create_task(task: Annotated[BaseTaskSchema, ...], db: Session = DB_SESSION):
    new_task = TaskModel(
        title=task.title,
        description=task.description,
        is_completed=task.is_completed,
    )
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
@router.put("/{task_id}")
async def update_task(
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
@router.delete("/{task_id}")
async def delete_task(
    task_id: Annotated[int, Path(gt=0)],
    db: Session = DB_SESSION,
):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    deleted_task = {"id": task.id, "title": task.title, "description": task.description}

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully", "deleted_task": deleted_task}
