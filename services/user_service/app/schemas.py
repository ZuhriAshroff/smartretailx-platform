from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class UserAdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(pattern="^(customer|admin|warehouse_staff)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RoleUpdate(BaseModel):
    role: str = Field(pattern="^(customer|admin|warehouse_staff)$")


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class PaginatedUsers(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserPublic]
