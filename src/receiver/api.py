import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from receiver.config import init_config

_LOG = logging.getLogger(__name__)

config = init_config()


app = FastAPI()


@app.get("/", response_class=RedirectResponse)
async def redirect_to_docs():
    return RedirectResponse("/docs")


@app.get("/probe/live")
async def liveness_probe():
    return {"status": "ok"}
