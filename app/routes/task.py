from http.client import HTTPException

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.email import send_email
from app.utils.deps import get_current_user

router = APIRouter(tags=["Tasks"])

@router.post("/")
def create_task(task: schemas.TaskCreate, bg: BackgroundTasks,db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    try:
        task_dict = task.dict()
        task_dict['created_by'] = current_user.id

        new_task = models.Task(**task_dict, position=0)
        db.add(new_task)

        db.commit()
        db.refresh(new_task)

        user = db.query(models.User).filter(models.User.id == new_task.assignee_id).first()

        if user:
            bg.add_task(
                send_email,
                user.email,
                "Task Created",
                f"Task '{new_task.title}' assigned to you"
            )

        return new_task

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.put("/move")
def move_task(data: schemas.MoveTask, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    task = db.query(models.Task).filter(models.Task.id == data.task_id).first()

    if task.project_id != data.project_id:
        raise HTTPException(400, "Invalid project")

    task.column_id = data.new_column_id
    task.position = data.new_position

    db.commit()

    return {"message": "Moved"}

@router.delete("/{task_id}")
def delete_task(task_id: int,
                bg: BackgroundTasks,
                db: Session = Depends(get_db),
                current_user = Depends(get_current_user)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    db.delete(task)
    db.commit()

    user = db.query(models.User).filter(models.User.id == task.assignee_id).first()

    if user:
        bg.add_task(
            send_email,
            user.email,
            "Task Deleted",
            f"Task '{task.title}' deleted"
        )

        return {"message": "Deleted"}

@router.get("/")
def get_tasks(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    tasks = db.query(models.Task).filter(
        models.Task.project_id == project_id
    ).all()

    return tasks

@router.put("/{task_id}")
def update_task(task_id: int,data: schemas.TaskUpdate, bg: BackgroundTasks, db: Session = Depends(get_db),current_user = Depends(get_current_user)):

    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == task.project_id,
        models.ProjectMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not allowed")

    old_column = task.column_id
    old_assignee = task.assignee_id

    for key, value in data.dict(exclude_unset=True).items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)

    if old_assignee != task.assignee_id:
        user = db.query(models.User).filter(models.User.id == task.assignee_id).first()
        if user:
            bg.add_task(
                send_email,
                user.email,
                "Task Assigned",
                f"You got assigned: {task.title}"
            )

    if old_column != task.column_id:
        bg.add_task(
            send_email,
            current_user.email,
            "Task Moved",
            f"Task '{task.title}' moved"
        )

    return task