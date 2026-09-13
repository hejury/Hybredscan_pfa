from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    username: str
    # True only for the synthetic local-bypass session (api/dependencies.py
    # ::get_current_user, always on for 127.0.0.1/localhost/::1) -- never
    # true for a real, cookie-backed login.
    is_local_session: bool = False


class RegisterResponse(BaseModel):
    success: bool
    message: str
