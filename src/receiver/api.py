import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    Security,
    status,
)
from fastapi.responses import RedirectResponse
from fastapi.security.api_key import APIKeyHeader
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

    _LOG.info("Connected to NATS")

    yield

    await client.close()


api_key_header = APIKeyHeader(name="X-Telegram-Bot-Api-Secret-Token")
app = FastAPI(lifespan=lifespan)


async def verify_telegram_token(token: str = Security(api_key_header)) -> None:
    if token != config.secret_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def publish(bot_name: str, update: bytes) -> None:
    _LOG.debug("Publishing update for bot %s", bot_name)
    jetstream = client.jetstream()
    await jetstream.publish(
        subject=f"{config.nats.stream_name}.{bot_name}",
        stream=config.nats.stream_name,
        payload=update,
    )


@app.get("/", response_class=RedirectResponse)
async def redirect_to_docs():
    return RedirectResponse("/docs")


@app.get("/probe/live")
async def liveness_probe():
    return {"status": "ok"}


@app.post(
    "/update/{bot_name}",
    status_code=status.HTTP_202_ACCEPTED,
    response_class=Response,
)
async def receive_update(
    bot_name: str,
    _: Annotated[None, Security(verify_telegram_token)],
    request: Request,
) -> Response:
    await publish(bot_name, await request.body())
    return Response(status_code=status.HTTP_202_ACCEPTED)
