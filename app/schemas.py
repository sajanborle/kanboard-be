from datetime import datetime

from pydantic import BaseModel
from typing import Optional
from enum import Enum

class RoleEnum(str, Enum):
    Admin = "Admin"
    Developer = "Developer"
    Sales = "Sales"
    Client = "Client"
    Devops = "Devops"
    Tester = "Tester"


class PriorityEnum(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"
    Critical = "Critical"

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    role: Optional[RoleEnum] = RoleEnum.Developer

class UserLogin(BaseModel):
    email: str
    password: str
    
class ProjectCreate(BaseModel):
    name: str
    description: str

class InviteUser(BaseModel):
    email: str
    role: RoleEnum

class TaskCreate(BaseModel):
    title: str
    description: str
    column_id: int
    priority: PriorityEnum
    assignee_id: int
    project_id: int
    category: Optional[str] = None
    sub_category: Optional[str] = None

    estimate_time: Optional[int] = None
    completed_time: Optional[int] = None
    due_date: Optional[str] = None

class MoveTask(BaseModel):
    task_id: int
    project_id: int
    new_column_id: int
    new_position: int

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    column_id: Optional[int] = None
    priority: Optional[PriorityEnum] = None
    assignee_id: Optional[int] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    class Config:
        extra = "forbid"   
    estimate_time: Optional[int] = None
    completed_time: Optional[int] = None
    due_date: Optional[datetime] = None   
    
class ColumnCreate(BaseModel):
    name: str
    project_id: int