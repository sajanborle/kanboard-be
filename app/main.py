from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
from app.database import Base, engine
from app.routes import auth_routes, project, task, user, column

Base.metadata.create_all(bind=engine)

app = FastAPI(swagger_ui_init_oauth=None)

app.include_router(auth_routes.router, prefix="/auth")
app.include_router(project.router, prefix="/projects")
app.include_router(task.router, prefix="/tasks")
app.include_router(user.router, prefix="/users")
app.include_router(column.router, prefix="/columns")
