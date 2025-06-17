import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from nats.aio.client import Client

from receiver.config import init_config

_LOG = logging.getLogger(__name__)

config = init_config()
client = Client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.connect(
        config.nats.url,
        allow_reconnect=True,
    )

    yield

    await client.close()


app = FastAPI(lifespan=lifespan)


async def publish(bot_name: str, update: dict[str, Any]) -> None:
    jetstream = client.jetstream()
    await jetstream.publish(
        subject=f"{config.nats.subject_namespace}.{bot_name}",
        stream=config.nats.stream_name,
        payload=json.dumps(update).encode(),
    )


@app.get("/", response_class=RedirectResponse)
async def redirect_to_docs():
    return RedirectResponse("/docs")


@app.get("/probe/live")
async def liveness_probe():
    return {"status": "ok"}
