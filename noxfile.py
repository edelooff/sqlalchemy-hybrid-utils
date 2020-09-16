import nox


@nox.session(python="3.8")
def lint(session):
    session.install("flake8", "flake8-black", "flake8-bugbear", "flake8-isort")
    session.run("flake8", *session.posargs)


@nox.session(python="3.8")
def type(session):
    session.install("mypy", "sqlalchemy-stubs")
    session.run("mypy", *session.posargs)


@nox.session(python="3.8")
@nox.parametrize("sqlalchemy", ["1.0", "1.1", "1.2", "1.3"])
def test(session, sqlalchemy):
    args = session.posargs or ["--cov"]
    session.install("pytest", "coverage[toml]", "pytest-cov")
    session.install(f"sqlalchemy=={sqlalchemy}")
    session.install(".")
    session.run("pytest", *args)
