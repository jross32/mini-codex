from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: str = Field(min_length=2, max_length=100)

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class QuestCreateSchema(BaseModel):
    type: str
    title: str
    description: Optional[str] = ''
    xp_reward: int = 10
    stat_targets: Dict[str, Any] = {}
    due_date: Optional[str] = None
    is_active: bool = True
