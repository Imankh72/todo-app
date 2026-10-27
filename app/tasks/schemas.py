from pydantic import BaseModel, Field


class BaseTaskSchema(BaseModel):
    title: str = Field(min_length=4, max_length=64)
    description: str | None = Field(max_length=500)
    is_completed: bool = Field(default=False)
    user_id: int = Field(gt=0)


class TaskResponseSchema(BaseTaskSchema):
    id: int
