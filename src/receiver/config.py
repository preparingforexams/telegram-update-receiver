import logging
from dataclasses import dataclass
from typing import Self

import sentry_sdk
from bs_config import Env

_LOG = logging.getLogger(__name__)


@dataclass
class Config:
    app_version: str
    sentry_dsn: str | None

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            app_version=env.get_string("APP_VERSION", default="dev"),
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
