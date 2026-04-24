from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    role: Optional[str] = "Developer"   

class UserLogin(BaseModel):
    email: str
    password: str
    
class ProjectCreate(BaseModel):
    name: str
    description: str

class InviteUser(BaseModel):
    email: str
    role: str

class TaskCreate(BaseModel):
    title: str
    description: str
    column_id: int
    priority: str
    assignee_id: int
    project_id: int   
    created_by: Optional[int] = None

class MoveTask(BaseModel):
    task_id: int
    project_id: int
    new_column_id: int
    new_position: int

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    column_id: Optional[int] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[str] = None
    time_estimate: Optional[int] = None
    
class ColumnCreate(BaseModel):
    name: str
    project_id: int