import nox


def install_package_version(
    session: nox.Session,
    package: str,
    version: str
) -> None:
    if version == "latest":
        session.install(package)
    else:
        session.install(f"{package}=={version}")


TEST_DEPS = [
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
]

TEST_CMD = [
    "pytest",
    "--cov=quart_dishka",
    "--cov-append",
    "--cov-report=term-missing",
    "-v",
]

PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]
QUART_VERSIONS = ["0.20.0", "latest"]
DISHKA_VERSIONS = ["1.4.0", "latest"]


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv", reuse_venv=True, tags=["ci"])
@nox.parametrize("quart", QUART_VERSIONS)
@nox.parametrize("dishka", DISHKA_VERSIONS)
def run_all_tests(session: nox.Session, quart: str, dishka: str) -> None:
    session.install(*TEST_DEPS)
    
    install_package_version(session, "quart", quart)
    install_package_version(session, "dishka", dishka)
    
    session.install("-e", ".")
    
    session.run(*TEST_CMD, "tests")


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv", reuse_venv=True, tags=["latest"])
def latest_tests(session: nox.Session) -> None:
    session.install(*TEST_DEPS)

    install_package_version(session, "quart", "latest")
    install_package_version(session, "dishka", "latest")

    session.install("-e", ".")

    session.run(*TEST_CMD, "tests")
