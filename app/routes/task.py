from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app import models, schemas
from datetime import datetime, timedelta
from app.utils.email import send_email
from app.utils.deps import get_current_user
from sqlalchemy.orm.attributes import flag_modified
from app.utils.response import success_response
from app.utils.timezone import get_ist_time

router = APIRouter(tags=["Tasks"])

ACTION_CONFIG = {
    "created": {"icon": "🎯", "text": "created task"},
    "updated": {"icon": "✏️", "text": "updated task"},
    "assigned": {"icon": "👤", "text": "assigned task"},
    "moved": {"icon": "📦", "text": "moved task"},
    "deleted": {"icon": "❌", "text": "deleted task"},
}
def build_snapshot(task, column_name, current_username):
    return {
        "status": column_name,   
        "assignee": current_username,
        "estimate_time": f"{task.estimate_time} hours" if task.estimate_time else None,
        "completed_time": f"{task.completed_time} hours" if task.completed_time else None
    }


@router.post("/")
async def create_task(
    task: schemas.TaskCreate,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        task_dict = task.dict()

        result = await db.execute(
            select(models.BoardColumn).where(
                models.BoardColumn.project_id == task.project_id,
                models.BoardColumn.name == "Sales"
            )
        )
        column = result.scalar_one_or_none()

        if not column:
            raise HTTPException(404, "Sales column not found")

        task_dict["column_id"] = column.id

        if task_dict["priority"] == "Critical":
            hours = 12
        elif task_dict["priority"] == "High":
            hours = 24
        else:
            hours = 48

        task_dict["due_date"] = get_ist_time() + timedelta(hours=hours)

        task_dict["created_by"] = current_user.id

        new_task = models.Task(**task_dict, position=0)

        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        result = await db.execute(
            select(models.User).where(models.User.id == new_task.assignee_id)
        )
        assignee = result.scalar_one_or_none()
        snapshot = build_snapshot(
            new_task,
            column.name,
            current_user.username
        )

        await create_or_update_activity(db, new_task, current_user, snapshot)

        due_date = new_task.due_date.strftime("%d %b %Y %I:%M %p")
        created_at = new_task.created_at.strftime("%d %b %Y %I:%M %p")

        email_body = f"""
        <html>
        <body style="font-family: Arial; background:#f4f6f8; padding:20px;">

        <div style="background:white; padding:20px; border-radius:10px;">

        <h2 style="color:#333;">🚀 Task Notification</h2>

        <p><b>📌 Title:</b> {new_task.title}</p>
        <p><b>📝 Description:</b> {new_task.description}</p>

        <hr>

        <p><b>📂 Category:</b> {new_task.category or 'N/A'}</p>
        <p><b>📁 Sub Category:</b> {new_task.sub_category or 'N/A'}</p>

        <p>
        <b>⚡ Priority:</b>
        {new_task.priority}
        </span>
        </p>

        <p><b>📊 Column:</b> {column.name}</p>

        <p><b>⏳ Estimate Time:</b> {new_task.estimate_time or 0} hrs</p>

        <p><b>📅 Due Date:</b> {due_date}</p>
        <p><b>🕒 Created At:</b> {created_at}</p>

        <hr>

        <p><b>👤 Assigned By:</b> {current_user.email}</p>

        </div>

        </body>
        </html>
        """

        if assignee:
            bg.add_task(
                send_email,
                assignee.email,
                f"🚀 New Task: {new_task.title}",
                email_body
            )

        bg.add_task(
            send_email,
            current_user.email,
            f"Task Created: {new_task.title}",
            email_body
        )
        return success_response(
            data={"id": new_task.id, "title": new_task.title},
            message="Task created successfully"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))

@router.put("/move")
async def move_task(
    data: schemas.MoveTask,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Task).where(models.Task.id == data.task_id)
    )
    task = result.scalar_one_or_none()
    
    result_column = await db.execute(
            select(models.BoardColumn).where(models.BoardColumn.id == task.column_id)
        )
    column = result_column.scalar_one_or_none()
    
    result_assignee = await db.execute(
            select(models.User).where(models.User.id == task.assignee_id)
        )
    assignee = result_assignee.scalar_one_or_none()

    if not task:
        raise HTTPException(404, "Task not found")

    if task.project_id != data.project_id:
        raise HTTPException(400, "Invalid project")

    task.column_id = data.new_column_id
    task.position = data.new_position
    
    data = {
        "id": task.id,
        "title": task.title,
        "priority": task.priority,
        "column_name": column.name if column else "N/A",
        "assignee_id": task.assignee_id,
        "assignee_username": assignee.username if assignee else "N/A",
        "due_date": task.due_date.strftime("%d %b %Y %I:%M %p") if task.due_date else "N/A",
        "created_at": task.created_at.strftime("%d %b %Y %I:%M %p")
    }
    
    email_body = f"""
        <html>
        <body style="font-family: Arial; background:#f4f6f8; padding:20px;">
        <div style="background:white; padding:20px; border-radius:10px;">

        <h2 style="color:red;">❌ Task Deleted</h2>

        <p><b>📌 Title:</b> {task.title}</p>
        <p><b>📝 Description:</b> {task.description}</p>

        <hr>

        <p><b>📂 Category:</b> {task.category or 'N/A'}</p>
        <p><b>📁 Sub Category:</b> {task.sub_category or 'N/A'}</p>

        <p>
        <b>⚡ Priority:</b>
        {task.priority}
        </span>
        </p>

        <p><b>📊 Column:</b> {column.name if column else 'N/A'}</p>

        <p><b>⏳ Estimate Time:</b> {task.estimate_time or 0} hrs</p>

        <p><b>📅 Due Date:</b> {data.get("due_date")}</p>
            <p><b>🕒 Created At:</b> {data.get("created_at")}</p>

        <hr>

        <p><b>👤 Moved Task By:</b> {current_user.email}</p>

        </div>
        </body>
        </html>
        """
    snapshot = build_snapshot(
        task,
        column.name,
        current_user.username
    )

    await create_or_update_activity(db, task, current_user, snapshot)

    await db.commit()
    return success_response(data=data, message="Task moved successfully")


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        # 🔹 get task
        result = await db.execute(
            select(models.Task).where(models.Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(404, "Task not found")

        # 🔹 get assignee
        result = await db.execute(
            select(models.User).where(models.User.id == task.assignee_id)
        )
        assignee = result.scalar_one_or_none()

        # 🔹 get column
        result = await db.execute(
            select(models.BoardColumn).where(models.BoardColumn.id == task.column_id)
        )
        column = result.scalar_one_or_none()

        due_date = task.due_date.strftime("%d %b %Y %I:%M %p") if task.due_date else "N/A"
        created_at = task.created_at.strftime("%d %b %Y %I:%M %p")

        email_body = f"""
        <html>
        <body style="font-family: Arial; background:#f4f6f8; padding:20px;">
        <div style="background:white; padding:20px; border-radius:10px;">

        <h2 style="color:red;">❌ Task Deleted</h2>

        <p><b>📌 Title:</b> {task.title}</p>
        <p><b>📝 Description:</b> {task.description}</p>

        <hr>

        <p><b>📂 Category:</b> {task.category or 'N/A'}</p>
        <p><b>📁 Sub Category:</b> {task.sub_category or 'N/A'}</p>

        <p>
        <b>⚡ Priority:</b>
        {task.priority}
        </span>
        </p>

        <p><b>📊 Column:</b> {column.name if column else 'N/A'}</p>

        <p><b>⏳ Estimate Time:</b> {task.estimate_time or 0} hrs</p>

        <p><b>📅 Due Date:</b> {due_date}</p>
        <p><b>🕒 Created At:</b> {created_at}</p>

        <hr>

        <p><b>👤 Deleted By:</b> {current_user.email}</p>

        </div>
        </body>
        </html>
        """
        snapshot = build_snapshot(
            task,
            "Deleted",
            current_user.username
        )

        await create_or_update_activity(db, task, current_user, snapshot)
        # 🔹 delete task
        await db.delete(task)
        await db.commit()

        if assignee:
            bg.add_task(
                send_email,
                assignee.email,
                f"Task Deleted: {task.title}",
                email_body
            )

        bg.add_task(
            send_email,
            current_user.email,
            f"Task Deleted: {task.title}",
            email_body
        )
        data = {
            "id": task.id,
            "title": task.title,
            "priority": task.priority,
            "column_name": column.name if column else "N/A",
        }

        return success_response(data=data, message="Task deleted successfully")

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))

@router.get("/")
async def get_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(models.Task).where(models.Task.project_id == project_id)
    )
    tasks = result.scalars().all()

    data = [
        {
            "id": t.id,
            "title": t.title,
            "priority": t.priority,
            "column_id": t.column_id,
            "assignee_id": t.assignee_id,
            "category": t.category,          
            "sub_category": t.sub_category,  
            "due_date": t.due_date
        }
        for t in tasks
    ]

    return success_response(data=data)


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    data: schemas.TaskUpdate,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(models.Task).where(models.Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(404, "Task not found")

        old_assignee = task.assignee_id
        old_column = task.column_id

        update_data = data.dict(exclude_unset=True)

        from datetime import datetime

        if "due_date" in update_data and update_data["due_date"]:
            if isinstance(update_data["due_date"], str):
                update_data["due_date"] = datetime.fromisoformat(update_data["due_date"])

        for key, value in update_data.items():
            setattr(task, key, value)

        await db.commit()
        await db.refresh(task)

        result = await db.execute(
            select(models.User).where(models.User.id == task.assignee_id)
        )
        assignee = result.scalar_one_or_none()


        result = await db.execute(
            select(models.BoardColumn).where(models.BoardColumn.id == task.column_id)
        )
        column = result.scalar_one_or_none()

        due_date = task.due_date.strftime("%d %b %Y %I:%M %p") if task.due_date else "N/A"
        created_at = task.created_at.strftime("%d %b %Y %I:%M %p")

        email_body = f"""
        <html>
        <body style="font-family: Arial; background:#f4f6f8; padding:20px;">
        <div style="background:white; padding:20px; border-radius:10px;">

        <h2>🔄 Task Updated</h2>

        <p><b>📌 Title:</b> {task.title}</p>
        <p><b>📝 Description:</b> {task.description}</p>

        <hr>

        <p><b>📂 Category:</b> {task.category or 'N/A'}</p>
        <p><b>📁 Sub Category:</b> {task.sub_category or 'N/A'}</p>

        <p>
        <b>⚡ Priority:</b>
        {task.priority}
        </span>
        </p>

        <p><b>📊 Column:</b> {column.name if column else 'N/A'}</p>

        <p><b>⏳ Estimate Time:</b> {task.estimate_time or 0} hrs</p>

        <p><b>📅 Due Date:</b> {due_date}</p>
        <p><b>🕒 Created At:</b> {created_at}</p>

        <hr>

        <p><b>👤 Updated By:</b> {current_user.email}</p>

        </div>
        </body>
        </html>
        """

        if old_assignee != task.assignee_id and assignee:
            bg.add_task(
                send_email,
                assignee.email,
                f"👤 Task Assigned: {task.title}",
                email_body
            )

        if old_column != task.column_id:
            bg.add_task(
                send_email,
                current_user.email,
                f"📦 Task Moved: {task.title}",
                email_body
            )

        if update_data:
            bg.add_task(
                send_email,
                current_user.email,
                f"✏️ Task Updated: {task.title}",
                email_body
            )
        
        snapshot = build_snapshot(
            task,
            "Close",
            current_user.username
        )

        await create_or_update_activity(db, task, current_user, snapshot)

        return success_response(
            data={"id": task.id, "title": task.title},
            message="Task updated successfully"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, str(e))

async def create_or_update_activity(db, task, user, snapshot):
    result = await db.execute(
        select(models.ActivityLog).where(models.ActivityLog.task_id == task.id)
    )
    log = result.scalar_one_or_none()

    if log:
        history = log.history or []
        history.append(snapshot)
        log.history = history

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(log, "history")  

    else:
        log = models.ActivityLog(
            task_id=task.id,
            project_id=task.project_id,
            user_id=user.id,
            action="history",
            history=[snapshot]
        )
        db.add(log)

    await db.commit()
        
@router.get("/{task_id}/history")
async def get_history(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.ActivityLog).where(models.ActivityLog.task_id == task_id)
    )
    log = result.scalar_one_or_none()

    return success_response(
        data=log.history if log else []
    )