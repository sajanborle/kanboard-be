from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
from app.database import Base, engine
from app.routes import auth, project, task, user, column


Base.metadata.create_all(bind=engine)

app = FastAPI(swagger_ui_init_oauth=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    )


app.include_router(auth.router, prefix="/api/auth")
app.include_router(project.router, prefix="/api/projects")
app.include_router(task.router, prefix="/api/tasks")
app.include_router(user.router, prefix="/api/users")
app.include_router(column.router, prefix="/api/columns")
