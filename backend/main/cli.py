from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from alembic.config import CommandLine as AlembicCLI
from alembic.config import Config as AlembicConfig

from backend.infra.database.alembic import ALEMBIC_CONFIG
from backend.infra.database.config import DatabaseConfig

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


def run_alembic(options: Namespace) -> None:
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


def main() -> None:
    parser = create_parser()
    options = parser.parse_args()

    cmd_map: dict[str, Callable[[Namespace], None]] = {
        "alembic": run_alembic,
    }
    cmd_map[options.which](options)
