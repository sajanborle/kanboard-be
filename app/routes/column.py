from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app import models, schemas
from app.utils.deps import get_current_user
from app.utils.response import success_response

router = APIRouter(tags=["Columns"])


@router.post("/")
async def create_column(
    data: schemas.ColumnCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # check project exists
    result = await db.execute(
        select(models.Project).where(models.Project.id == data.project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    column = models.BoardColumn(
        name=data.name,
        project_id=data.project_id
    )

    db.add(column)
    await db.commit()
    await db.refresh(column)

    return success_response(
        data={
            "id": column.id,
            "name": column.name,
            "project_id": column.project_id
        },
        message="Column created successfully"
    )


@router.get("/")
async def get_all_columns(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(select(models.BoardColumn))
    columns = result.scalars().all()

    data = [
        {
            "id": c.id,
            "name": c.name,
            "project_id": c.project_id
        }
        for c in columns
    ]

    return success_response(
        data=data,
        message="Columns fetched successfully"
    )


@router.get("/{project_id}/columns")
async def get_project_columns(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(models.BoardColumn)
        .where(models.BoardColumn.project_id == project_id)
        .order_by(models.BoardColumn.id)
    )
    columns = result.scalars().all()

    data = [
        {
            "id": c.id,
            "name": c.name
        }
        for c in columns
    ]

    return success_response(
        data=data,
        message="Project columns fetched successfully"
    )
    
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
