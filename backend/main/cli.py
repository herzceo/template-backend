from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from alembic.config import CommandLine as AlembicCLI
from alembic.config import Config as AlembicConfig

from backend.entry.rest.main import APIConfig, run_api
from backend.infra.database.alembic import ALEMBIC_CONFIG
from backend.infra.database.config import DatabaseConfig
from backend.infra.external.http.discord.config import DiscordOAuthSettings
from backend.infra.external.http.github.config import GitHubOAuthSettings
from backend.infra.external.http.google_oauth.config import GoogleOAuthSettings
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


def cmd_run_api(_options: Namespace) -> None:
    run_api(
        load_from_env(APIConfig),
        load_from_env(DatabaseConfig),
        oauth_state_config=load_from_env(OAuthStateConfig),
        google_oauth_settings=load_from_env(GoogleOAuthSettings),
        github_settings=load_from_env(GitHubOAuthSettings),
        discord_settings=load_from_env(DiscordOAuthSettings),
    )


def main() -> None:
    parser = create_parser()
    options = parser.parse_args()

    cmd_map: dict[str, Callable[[Namespace], None]] = {
        "alembic": cmd_run_alembic,
        "api": cmd_run_api,
    }
    cmd_map[options.which](options)
