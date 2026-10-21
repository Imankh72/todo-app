from pydantic import BaseModel, Field


class BaseTaskSchema(BaseModel):
    title: str = Field(min_length=4, max_length=64)
    description: str = Field(max_length=500)
    is_completed: bool = Field(default=False)


class TaskResponseSchema(BaseTaskSchema):
    id: str
