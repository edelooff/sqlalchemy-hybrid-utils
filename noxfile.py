import nox


@nox.session(python="3.8")
def black(session):
    args = session.posargs or (".",)
    session.install("black")
    session.run("black", "--check", *args)


@nox.session(python="3.8")
def flake(session):
    session.install("flake8")
    session.run("flake8", *session.posargs)


@nox.session(python="3.8")
def mypy(session):
    session.install("mypy", "sqlalchemy-stubs")
    session.run("mypy", *session.posargs)


@nox.session(python="3.8")
@nox.parametrize("sqla", ["1.1", "1.2", "1.3"])
def tests(session, sqla):
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.install(f"sqlalchemy=={sqla}")
    session.run("pytest", *args)
