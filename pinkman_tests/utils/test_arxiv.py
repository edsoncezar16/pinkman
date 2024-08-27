from pinkman.utils.arxiv_helpers import paginate
from pinkman.dlt.sources.arxiv.settings import ARXIV_TIMEZONE, WAIT_TIME
import pendulum
import pytest
from requests.exceptions import HTTPError


def test_paginate(params, max_entries):
    feeds = paginate(params, max_entries, WAIT_TIME)

    first_feed = next(feeds)
    assert (
        first_feed.feed.title
        == "ArXiv Query: search_query=all:electron&amp;id_list=&amp;start=0&amp;max_results=10"
    )
    assert first_feed.feed.id == "http://arxiv.org/api/WyBPOs+pRgzCTXTMWhtnbcOmk6g"
    assert first_feed.feed.updated == pendulum.today(ARXIV_TIMEZONE).to_rfc3339_string()
    assert first_feed.feed.opensearch_startindex == "0"
    assert first_feed.feed.opensearch_itemsperpage == "10"

    entries = first_feed.entries
    assert len(entries) == 10

    first_entry = entries[0]
    assert first_entry.id == "http://arxiv.org/abs/cs/9301112v1"
    assert first_entry.published == "1990-04-01T00:00:00Z"
    assert first_entry.title == "A note on digitized angles"
    assert first_entry.author == "Donald E. Knuth"
    assert first_entry.category == "cs.GR"
    assert (
        first_entry.arxiv_journal_ref
        == "Electronic Publishing 3 (1990), no. 2, 99--104"
    )
    assert sum((1 for _ in feeds)) + 1 == 10


def test_bad_api_call():
    with pytest.raises(HTTPError):
        next(
            paginate(
                params={"id_list": "1234"},
                max_entries=0,
                wait_time=WAIT_TIME,
            )
        )

    with pytest.raises(ValueError, match="feed with invalid entries"):
        next(
            paginate(
                params={"id_list": "1234.12345"}, max_entries=0, wait_time=WAIT_TIME
            )
        )
