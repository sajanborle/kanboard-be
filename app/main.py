import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, project, task, user, column

load_dotenv()

app = FastAPI(swagger_ui_init_oauth=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS").split(",")],
    allow_credentials=os.getenv("ALLOWED_CREDENTIALS").lower() == "true",
    allow_methods=["*"],   
    allow_headers=["*"],   
)


app.include_router(auth.router, prefix="/api/auth")
app.include_router(project.router, prefix="/api/projects")
app.include_router(task.router, prefix="/api/tasks")
app.include_router(user.router, prefix="/api/users")
app.include_router(column.router, prefix="/api/columns")
