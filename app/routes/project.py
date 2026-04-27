from fastapi import APIRouter, Depends, Header, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.email import send_email
from app.utils.deps import get_current_user
from app.utils.response import success_response, error_response

router = APIRouter(tags=["Projects"])

@router.post("/")
def create_project(
    data: schemas.ProjectCreate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        project = models.Project(**data.dict(), created_by=current_user.id)
        db.add(project)
        db.flush()

        create_default_columns(db, project.id)

        db.commit()  
        bg.add_task(
            send_email,
            current_user.email,
            "Project Created",
            f"Project '{project.name}' created successfully"
        )

        return success_response(
            data=project,
            message="Project created successfully"
        )

    except Exception as e:
        db.rollback()  
        raise HTTPException(500, str(e))

def create_default_columns(db, project_id):
    default_cols = [
        "Backlog",
        "In Progress",
        "Review",
        "Testing",
        "Done"
    ]

    for index, col in enumerate(default_cols):
        db.add(models.BoardColumn(
            name=col,
            project_id=project_id
        ))

    db.commit()
@router.post("/{project_id}/invite")
def invite(
    project_id: int,
    data: schemas.InviteUser,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(404, "User not found")

    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:
        raise HTTPException(404, "Project not found")

    member = models.ProjectMember(
        user_id=user.id,
        project_id=project_id,
        role=data.role
    )

    db.add(member)
    db.commit()

    bg.add_task(
        send_email,
        user.email,
        "Project Invitation",
        f"""
            Hello {user.username},

            You have been invited to the project:

            📌 Project: {project.name}
            📝 Description: {project.description}
            👤 Role: {data.role}

            Invited by: {current_user.email}

            Please login to view the project.

            Thanks,
            Kanban Team
            """
    )

    return success_response(
            data={"project": project.name},
            message="User invited successfully"
        )

@router.get("/{project_id}/tasks")
def get_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    tasks = db.query(models.Task, models.BoardColumn.name).join(
        models.BoardColumn, models.Task.column_id == models.BoardColumn.id
    ).filter(
        models.Task.project_id == project_id
    ).all()

    result = [
        {
            "id": t.Task.id,
            "title": t.Task.title,
            "column": t.name,
            "column_id": t.Task.column_id,
            "priority": t.Task.priority
        }
        for t in tasks
    ]

    return success_response(
        data=result,
        message="Tasks fetched successfully"
    )
            
@router.get("/")
def get_projects(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    projects = db.query(models.Project).all()
    return success_response(data=projects)