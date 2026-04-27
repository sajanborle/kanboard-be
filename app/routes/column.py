from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.deps import get_current_user
from app.utils.response import success_response

router = APIRouter(tags=["Columns"])

@router.post("/")
def create_column(data: schemas.ColumnCreate,db: Session = Depends(get_db),current_user = Depends(get_current_user)):

    # 🔒 Optional: check project exists
    project = db.query(models.Project).filter(models.Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    column = models.BoardColumn(
        name=data.name,
        project_id=data.project_id
    )

    db.add(column)
    db.commit()
    db.refresh(column)

    return success_response(data=column, message="Column created successfully")


@router.get("/")
def get_all_columns(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    columns = db.query(models.BoardColumn).all()

    result = [
        {
            "id": c.id,
            "name": c.name
        }
        for c in columns
    ]
    return success_response(data=result, message="Columns fetched successfully")

@router.get("/{project_id}/columns")
def get_project_columns(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    columns = db.query(models.BoardColumn).filter(
        models.BoardColumn.project_id == project_id
    ).all()
    result = [
        {
            "id": c.id,
            "name": c.name
        }
        for c in columns
    ]
    return success_response(data=result, message="Project columns fetched successfully")