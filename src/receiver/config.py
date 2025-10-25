import logging
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Self

import sentry_sdk
from bs_config import Env

if TYPE_CHECKING:
    from collections.abc import Set

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class NatsConfig:
    url: str
    stream_name: str

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            url=env.get_string("server-url", required=True),
            stream_name=env.get_string("stream-name", required=True),
        )


@dataclass(frozen=True, kw_only=True)
class Config:
    app_version: str
    bot_config_path: Path
    nats: NatsConfig
    secret_token: str
    sentry_dsn: str | None

    @property
    @cache
    def __bot_configs(self) -> Env:
        env = Env.load(
            toml_configs=[self.bot_config_path],
        )
        return env / "bot-config"

    @cache
    def get_required_keys(self, bot_name: str) -> Set[str]:
        bot_config = self.__bot_configs / bot_name
        return set(bot_config.get_string_list("required-keys", default=[]))

    @classmethod
    def from_env(cls, env: Env) -> Self:
        return cls(
            app_version=env.get_string("app-version", default="dev"),
            bot_config_path=env.get_string(
                "bot-config-path",
                required=True,
                transform=Path,
            ),
            nats=NatsConfig.from_env(env / "nats"),
            secret_token=env.get_string("secret-token", required=True),
            sentry_dsn=env.get_string("sentry-dsn"),
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
