import asyncio
import json
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import activity, auth, health, hosts, search, ws
from app.api.ws_manager import ws_manager
from app.core.config import get_settings
from app.core.database import Base, engine
from app.services.classifier import seed_default_rules
from app.core.database import SessionLocal

settings = get_settings()

REDIS_CHANNEL = "snapshot_updates"


async def _redis_listener() -> None:
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            host_id = data["host_id"]
            await ws_manager.broadcast(host_id, data)
        except Exception:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_rules(db)
    finally:
        db.close()

    listener = asyncio.create_task(_redis_listener())
    yield
    listener.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api/v1"
app.include_router(health.router, prefix=api_prefix)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(hosts.router, prefix=api_prefix)
app.include_router(activity.router, prefix=api_prefix)
app.include_router(search.router, prefix=api_prefix)
app.include_router(ws.router)
