import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True


@nox.session(tags=["tests"], python=["3.12.0", "3.13.0"])
def integration(session: nox.Session) -> None:
    install_args = [
        "uv",
        "sync",
        "--group=dev",
        "--frozen",
        "--no-default-groups",
        "--active",
    ]
    if session.python:
        install_args.append(f"--python={session.python}")
    session.run_install(*install_args)
    session.run("pytest", "tests/integration")


@nox.session(tags=["tests"])
def adapters(session: nox.Session) -> None:
    install_args = [
        "uv",
        "sync",
        "--group=dev",
        "--frozen",
        "--no-default-groups",
        "--active",
    ]
    if session.python:
        install_args.append(f"--python={session.python}")
    session.run_install(*install_args)
    session.run("pytest", "tests/integration/adapters", "-v")


@nox.session(tags=["tests"])
def unit(session: nox.Session) -> None:
    install_args = [
        "uv",
        "sync",
        "--group=dev",
        "--frozen",
        "--no-default-groups",
        "--active",
    ]
    if session.python:
        install_args.append(f"--python={session.python}")
    session.run_install(*install_args)
    session.run("pytest", "tests/unit", "-v")
