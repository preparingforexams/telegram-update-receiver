from bs_config import Env
from fastapi.testclient import TestClient
from pytest import fixture

from receiver.config import Config, NatsConfig


@fixture()
def config() -> Config:
    return Config(
        _bot_configs=Env.load_from_dict({}),
        app_version="",
        nats=NatsConfig(
            "http://localhost:4222",
            stream_name="telegram",
        ),
        secret_token="dummy",
        sentry_dsn="",
    )


@fixture()
def client(config, mocker) -> TestClient:  # type: ignore
    mocker.patch("receiver.config.init_config", return_value=config)
    from receiver.api import app

    client = TestClient(app)
    yield client
    client.close()
