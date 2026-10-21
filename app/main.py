from contextlib import asynccontextmanager

from core.database import get_db
from fastapi import Depends, FastAPI
from tasks.routes import router as tasks_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Todo Application",
    version="1.0.0",
    contact={"name": "Iman Khorshidi", "email": "imankhorshidi72@gmail.com"},
    lifespan=lifespan,
)


DB_SESSION = Depends(get_db)


app.include_router(tasks_routes)
