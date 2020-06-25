import nox


@nox.session(python="3.8")
def lint(session):
    session.install("flake8", "flake8-black")
    session.run("flake8", *session.posargs)


@nox.session(python="3.8")
def type(session):
    session.install("mypy", "sqlalchemy-stubs")
    session.run("mypy", *session.posargs)


@nox.session(python="3.8")
@nox.parametrize("sqla", ["1.1", "1.2", "1.3"])
def test(session, sqla):
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.install(f"sqlalchemy=={sqla}")
    session.run("pytest", *args)
