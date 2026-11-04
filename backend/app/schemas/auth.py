from pydantic import BaseModel, Field
from typing import Optional, List

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)

class UserRoleOut(BaseModel):
    school_id: int
    school_name: str
    udise_code: str
    role: str  # admin, teacher, counsellor
    assigned_classes: Optional[str] = None

class UserProfileOut(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    designation: Optional[str] = None
    roles: List[UserRoleOut]
    current_role: UserRoleOut

class LoginResponse(BaseModel):
    message: str
    user: UserProfileOut
    token: Optional[str] = None

