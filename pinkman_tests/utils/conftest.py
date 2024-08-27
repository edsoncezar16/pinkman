import pytest


@pytest.fixture
def params():
    return {
        "search_query": "all:electron",
        "sortBy": "submittedDate",
        "sortOrder": "ascending",
    }
