import logging
from dataclasses import dataclass
from typing import Self

import sentry_sdk
from bs_config import Env

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class NatsConfig:
    url: str
    stream_name: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            url=env.get_string("SERVER_URL", required=True),
            stream_name=env.get_string("STREAM_NAME", required=True),
        )


@dataclass(frozen=True)
class Config:
    _bot_configs: Env

    app_version: str
    nats: NatsConfig
    secret_token: str
    sentry_dsn: str | None

    def get_required_keys(self, bot_name: str) -> list[str]:
        return self._bot_configs.get_string_list(bot_name, default=[])

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            _bot_configs=env.scoped("BOT_CONFIG_"),
            app_version=env.get_string("APP_VERSION", default="dev"),
            nats=NatsConfig.from_env(env.scoped("NATS_")),
            secret_token=env.get_string("SECRET_TOKEN", required=True),
            sentry_dsn=env.get_string("SENTRY_DSN"),
        )


def _setup_logging(config: Config) -> None:
    logging.basicConfig()
    logging.getLogger(__package__).setLevel(logging.DEBUG)
    dsn = config.sentry_dsn
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            release=config.app_version,
        )
    else:
        _LOG.warning("Sentry is disabled")


def init_config() -> Config:
    env = Env.load(include_default_dotenv=True)
    config = Config.from_env(env)
    _setup_logging(config)
    return config
