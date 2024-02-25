import nox


@nox.session
def lint(session):
    session.install("flake8", "flake8-black", "flake8-bugbear", "flake8-isort")
    session.run("flake8", "src", "tests", *session.posargs)


@nox.session
def type(session):
    session.install("mypy", "sqlalchemy-stubs")
    session.run("mypy", *session.posargs)


@nox.session
@nox.parametrize("sqlalchemy", ["1.3", "1.4", "2.0"])
def test(session, sqlalchemy):
    args = session.posargs or ["--cov"]
    session.install("pytest", "coverage[toml]", "pytest-cov")
    session.install(f"sqlalchemy=={sqlalchemy}")
    session.install(".")
    session.run("pytest", *args)
