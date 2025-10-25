from pathlib import Path

from fastapi.testclient import TestClient
from pytest import fixture

from receiver.config import Config, NatsConfig


@fixture()
def config() -> Config:
    return Config(
        app_version="",
        bot_config_path=Path("bot-config.toml"),
        nats=NatsConfig(
            url="http://localhost:4222",
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
