from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="Developer")   
    
class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    created_by = Column(Integer)

class ProjectMember(Base):
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    project_id = Column(Integer)
    role = Column(String)

class BoardColumn(Base):
    __tablename__ = "columns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    column_id = Column(Integer)
    position = Column(Integer)
    priority = Column(String)
    assignee_id = Column(Integer)
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_by = Column(Integer, ForeignKey('users.id'))
    
