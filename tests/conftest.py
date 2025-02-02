import pytest

from .mocks import AppProvider, WebSocketAppProvider


@pytest.fixture
def app_provider():
    return AppProvider()


@pytest.fixture
def ws_app_provider():
    return WebSocketAppProvider()
