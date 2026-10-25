from pydantic import BaseModel, Field, field_validator


class UserLoginSchema(BaseModel):
    username: str = Field(min_length=4, max_length=64)
    password: str = Field(max_length=500)


class UserRegisterSchema(BaseModel):
    username: str = Field(min_length=4, max_length=64)
    password: str = Field(max_length=255)
    confirm_password: str = Field(max_length=255)

    @field_validator("confirm_password")
    def check_password_match(cls, confirm_password, validation):
        if not (confirm_password == validation.data.get("password")):
            raise ValueError("passwords doesn't match")
        return confirm_password
