import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated, Any

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


def _has_key(update: dict[str, Any], key: str) -> bool:
    parts = key.split(".")

    current: dict[str, Any] | Any = update
    for part in parts:
        if not isinstance(current, dict):
            return False

        value = current.get(part)
        if value is None:
            return False

        current = value

    return True


def _is_allowed(*, bot_name: str, body: bytes) -> bool:
    required_keys = config.get_required_keys(bot_name)
    if not required_keys:
        return True

    update = json.loads(body.decode("utf-8"))
    return all(_has_key(update, key) for key in required_keys)


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
    body = await request.body()

    if _is_allowed(bot_name=bot_name, body=body):
        await publish(bot_name, body)
    else:
        _LOG.debug("Update for bot %s was filtered out", bot_name)

    return Response(status_code=status.HTTP_202_ACCEPTED)
