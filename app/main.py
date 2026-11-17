from contextlib import asynccontextmanager

import httpx
from core.config import settings
from core.database import get_db
from fastapi import Depends, FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
from tasks.routes import router as tasks_routes
from users.routes import router as users_routes
from core.mail_util import send_email


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
app.include_router(users_routes)

redis = aioredis.from_url(settings.REDIS_URL)
cache_backend = RedisBackend(redis)
FastAPICache.init(cache_backend, prefix="fastapi-cache")


async def request_current_weather(latitude: float, longitude: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        current_weather = data.get("current_weather", {})
        return current_weather
    else:
        return None


@app.get("/weather", status_code=200)
@cache(expire=10)
async def fetch_current_weather(latitude: float = 40.7128, longitude: float = -74.0060):

    current_weather = await request_current_weather(latitude, longitude)
    if current_weather:
        return current_weather
    else:
        return "Failed to fetch current weather data"


@app.get("/send_email", status_code=200)
async def send_email_endpoint():
    await send_email(
        subject="Test Email",
        recipients=["recipients@example.com"],
        body="This is a test email sent from FastAPI",
    )
    return {"Message": "Email sent successfully"}
