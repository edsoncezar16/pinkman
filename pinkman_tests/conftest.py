import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "env_bk: mark test to run only in cicd environment, for example, tests requiring API keys",
    )


@pytest.fixture
def max_entries():
    return 100
