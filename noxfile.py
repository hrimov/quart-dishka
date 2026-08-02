import nox

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

# I aim to track the working state of all the supported versions
# https://devguide.python.org/versions/#supported-versions
PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14", "3.15"]
PYTHON_LEAST_STABLE_VERSION = "3.13"
PYTHON_MIN_VERSION = PYTHON_VERSIONS[0]
QUART_MIN_VERSION = "0.20.0"
DISHKA_VERSIONS = [
    "1.4.*",
    "1.5.*",
    "1.6.*",
    "1.7.*",
    "1.8.*",
    "1.9.*",
    "1.10.*",
    "latest",
]


def install_package_version(
    session: nox.Session,
    package: str,
    version: str,
) -> None:
    if version == "latest":
        session.install(package)
    else:
        session.install(f"{package}=={version}")


def run(
    session: nox.Session,
    *,
    quart: str,
    dishka: str,
) -> None:
    session.install(*TEST_DEPS)
    install_package_version(session, "quart", quart)
    install_package_version(session, "dishka", dishka)
    session.install("-e", ".")
    session.run(*TEST_CMD, "tests")


@nox.session(
    python=PYTHON_VERSIONS,
    venv_backend="uv",
    reuse_venv=True,
    tags=["ci", "python"],
)
def python_matrix(session: nox.Session) -> None:
    run(session, quart="latest", dishka="latest")


@nox.session(
    python=PYTHON_LEAST_STABLE_VERSION,
    venv_backend="uv",
    reuse_venv=True,
    tags=["ci", "dishka"],
)
@nox.parametrize("dishka", DISHKA_VERSIONS)
def dishka_matrix(session: nox.Session, dishka: str) -> None:
    run(session, quart="latest", dishka=dishka)


@nox.session(
    python=PYTHON_MIN_VERSION,
    venv_backend="uv",
    reuse_venv=True,
    tags=["ci"],
)
def floor(session: nox.Session) -> None:
    run(session, quart=QUART_MIN_VERSION, dishka="1.4.*")
