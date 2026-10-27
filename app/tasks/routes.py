from typing import Annotated

from auth.jwt_auth import get_authenticated_user
from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from users.models import UserModel

from tasks.models import TaskModel
from tasks.schemas import BaseTaskSchema

DB_SESSION = Depends(get_db)
USER_SESSION = Depends(get_authenticated_user)

router = APIRouter(tags=["tasks"], prefix="/tasks")


TaskId = Annotated[int, Path(gt=0)]


def get_task_or_404(
    db: Session,
    task_id: int,
    user: UserModel = USER_SESSION,
) -> TaskModel:
    query = select(TaskModel).where(
        TaskModel.id == task_id,
        TaskModel.user_id == user.id,
    )
    task = db.scalars(query).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# Get all tasks or search tasks by title
@router.get("/")
def get_tasks(
    q: Annotated[str | None, Query(alias="search", max_length=30)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    user: UserModel = USER_SESSION,
    db: Session = DB_SESSION,
):

    query = (
        select(TaskModel).filter(TaskModel.user_id == user.id).offset(skip).limit(limit)
    )

    if q:
        query = query.where(TaskModel.title.icontains(q, autoescape=True))
    return db.scalars(query).all()


# Get a task by its ID
@router.get("/{task_id}")
def get_task(task_id: TaskId, user: UserModel = USER_SESSION, db: Session = DB_SESSION):
    return get_task_or_404(db, task_id, user)


# Create a new task
@router.post("/", status_code=201)
def create_task(
    task: BaseTaskSchema, user: UserModel = USER_SESSION, db: Session = DB_SESSION
):
    new_task = TaskModel(**task.model_dump(exclude={"user_id"}), user_id=user.id)
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
            "user_id": user.id,
        },
    }


# Update a task by its ID
@router.put("/{task_id}")
def update_task(
    task_id: Annotated[int, Path(gt=0)],
    updated_task: BaseTaskSchema,
    user: UserModel = USER_SESSION,
    db: Session = DB_SESSION,
):
    task = (
        db.query(TaskModel)
        .filter(TaskModel.id == task_id, TaskModel.user_id == user.id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in updated_task.model_dump(exclude_unset=True).items():
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
            "user_id": task.user_id,
        },
    }


# Delete a task by its ID
@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: TaskId,
    user: UserModel = USER_SESSION,
    db: Session = DB_SESSION,
):

    task = get_task_or_404(db, task_id, user)
    db.delete(task)
    db.commit()
