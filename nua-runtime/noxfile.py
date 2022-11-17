import nox

# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]


@nox.session(python=PYTHON_VERSIONS)
def lint(session: nox.Session) -> None:
    with session.chdir("../nua-lib"):
        session.run("poetry", "install", external=True)
    session.run("poetry", "install", external=True)
    session.run("pip", "check", external=True)
    session.run("make", "lint", external=True)


@nox.session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    with session.chdir("../nua-lib"):
        session.run("poetry", "install", external=True)
    session.run("poetry", "install", external=True)
    session.run("pip", "check", external=True)
    session.run("pytest", "--tb=short", external=True)
