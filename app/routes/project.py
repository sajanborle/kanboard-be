from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app import models, schemas
from app.utils.email import send_email
from app.utils.deps import get_current_user
from app.utils.response import success_response

router = APIRouter(tags=["Projects"])


@router.post("/")
async def create_project(
    data: schemas.ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        project = models.Project(**data.dict(), created_by=current_user.id)

        db.add(project)
        await db.flush()

        await create_default_columns(db, project.id)

        await db.commit()
        await db.refresh(project)

        await send_email(
            current_user.email,
            "Project Created",
            f"""
                Hello {current_user.username},

                Your project has been created successfully

                📌 Project: {project.name}
                📝 Description: {project.description}

                Created by: {current_user.email}

                Thanks,
                Kanban Team
                """
        )

        return success_response(
            data={
                "id": project.id,
                "name": project.name,
                "description": project.description
            },
            message="Project created successfully"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))


async def create_default_columns(db: AsyncSession, project_id: int):
    default_cols = [
        "Admin",
        "Developer",
        "Sales",
        "Client",
        "Devops",
        "Tester",
        "Review",
        "Close"
    ]

    for col in default_cols:
        db.add(models.BoardColumn(
            name=col,
            project_id=project_id
        ))


@router.post("/{project_id}/invite")
async def invite(
    project_id: int,
    data: schemas.InviteUser,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(models.User).where(models.User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, "User not found")

    result = await db.execute(
        select(models.Project).where(models.Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(404, "Project not found")

    member = models.ProjectMember(
        user_id=user.id,
        project_id=project_id,
        role=data.role
    )

    db.add(member)
    await db.commit()

    bg.add_task(
        send_email,
        user.email,
        "Project Invitation",
        f"""
            Hello {user.username},

            You have been invited to the project:

            📌 Project: {project.name}
            📝 Description: {project.description}
            👤 Role: {member.role.value}

            Invited by: {current_user.email}

            Thanks,
            Kanban Team
            """
    )

    return success_response(
        data={"project": project.name},
        message="User invited successfully"
    )


@router.get("/{project_id}/tasks")
async def get_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Task, models.BoardColumn.name)
        .join(models.BoardColumn, models.Task.column_id == models.BoardColumn.id)
        .where(models.Task.project_id == project_id)
    )

    tasks = result.all()

    data = [
        {
            "id": t.Task.id,
            "title": t.Task.title,
            "column": t.name,
            "column_id": t.Task.column_id,
            "priority": t.Task.priority,
            "estimate_time": t.Task.estimate_time,
            "completed_time": t.Task.completed_time,
            "due_date": t.Task.due_date.isoformat() if t.Task.due_date else None
        }
        for t in tasks
    ]

    return success_response(
        data=data,
        message="Tasks fetched successfully"
    )


@router.get("/")
async def get_projects(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(select(models.Project))
    projects = result.scalars().all()

    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description
        }
        for p in projects
    ]

    return success_response(
        data=data,
        message="Projects fetched successfully"
    )