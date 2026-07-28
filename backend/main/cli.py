from argparse import ArgumentParser, Namespace
from os import environ
from typing import TYPE_CHECKING

from alembic.config import CommandLine as AlembicCLI
from alembic.config import Config as AlembicConfig

from backend.app.rest.v1.app_config import AppConfig, RateLimitConfig
from backend.app.rest.v1.services.session import SessionConfig
from backend.entry.queue import run_queue
from backend.entry.rest.main import APIConfig, run_api
from backend.infra.database.config import DatabaseConfig
from backend.infra.database.psql.alembic import ALEMBIC_CONFIG
from backend.infra.database.psql.dbus.config import QueueExecutorConfig
from backend.infra.database.redis import RedisConfig
from backend.infra.database.redis.adapters.config import LoginCodeConfig, VerificationConfig
from backend.infra.external.http.discord.config import DiscordOAuthConfig
from backend.infra.external.http.github.config import GitHubOAuthConfig
from backend.infra.external.http.google_oauth.config import GoogleOAuthConfig
from backend.infra.external.http.openrouter.config import OpenRouterConfig
from backend.infra.external.http.resend.config import ResendConfig
from backend.infra.security.config import OAuthStateConfig

from .utils import load_from_env

if TYPE_CHECKING:
    from collections.abc import Callable


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="backend", description="Core backend application")

    sub = parser.add_subparsers(dest="which", required=True)
    alembic_parent = AlembicCLI(prog="backend alembic").parser
    sub.add_parser(
        "alembic",
        parents=[alembic_parent],
        add_help=False,
        prog="backend alembic",
        formatter_class=alembic_parent.formatter_class,
    )
    sub.add_parser("api", prog="backend api")
    sub.add_parser("queue", prog="backend queue")

    return parser


def cmd_run_alembic(options: Namespace) -> None:
    db = load_from_env(DatabaseConfig)

    if options.config is None:
        options.config = ALEMBIC_CONFIG

    alembic_cli = AlembicCLI()
    cfg = AlembicConfig(
        file_=options.config,
        toml_file="pyproject.toml",
        ini_section=options.name,
        cmd_opts=options,
        config_args={"sqlalchemy.url": db.get_postgres_url()},
    )
    alembic_cli.run_cmd(cfg, options)


def cmd_run_queue(_options: Namespace) -> None:
    run_queue(
        load_from_env(QueueExecutorConfig),
        load_from_env(DatabaseConfig),
        load_from_env(ResendConfig),
        load_from_env(RedisConfig),
        load_from_env(VerificationConfig),
        load_from_env(LoginCodeConfig),
    )


def cmd_run_api(_options: Namespace) -> None:
    run_api(
        load_from_env(APIConfig),
        load_from_env(DatabaseConfig),
        redis_config=load_from_env(RedisConfig),
        verification_config=load_from_env(VerificationConfig),
        login_code_config=load_from_env(LoginCodeConfig),
        session_config=load_from_env(SessionConfig),
        app_config=load_from_env(AppConfig),
        rate_limit_config=load_from_env(RateLimitConfig),
        oauth_state_config=load_from_env(OAuthStateConfig),
        google_oauth_config=load_from_env(GoogleOAuthConfig),
        github_config=load_from_env(GitHubOAuthConfig),
        discord_config=load_from_env(DiscordOAuthConfig),
        openrouter_config=(
            load_from_env(OpenRouterConfig) if "OPENROUTER_API_KEY" in environ else None
        ),
    )


def main() -> None:
    parser = create_parser()
    options = parser.parse_args()

    cmd_map: dict[str, Callable[[Namespace], None]] = {
        "alembic": cmd_run_alembic,
        "api": cmd_run_api,
        "queue": cmd_run_queue,
    }
    cmd_map[options.which](options)
