import feedparser
from feedparser import FeedParserDict
from dlt.sources.helpers import requests
import logging
from typing import Any, Iterator
import time
from pinkman.dlt.sources.arxiv.settings import BASE_ARXIV_URL

logger = logging.getLogger(__name__)


def _is_valid_feed(feed: FeedParserDict) -> bool:
    """Checks if a feed contains valid entries for further processing.

    This has to do with possible bad calls of the ArXiv API.

    See https://info.arxiv.org/help/api/user-manual.html#34-errors.

    DISCLAIMER: The above documentation is just a starging point, as it is
    out of date and the example outputs do not correspond with current values
    when executing the http requests shown.

    The validity checks implemented here cover only known scenarios and will
    probably need to be modified in future releases.

    Args:
        feed: FeedParserDict: a feed returned from calling the ArXiv API.

    Returs:
        bool: whether the feed has valid child entries for further processing.
    """
    if len(feed.entries) == 0:
        return False

    def _has_valid_arxiv_id(entry: dict) -> bool:
        id: str = entry.get("id", "")
        return id.startswith("http://arxiv.org/abs/")

    return all(map(_has_valid_arxiv_id, feed.entries))


def _get_feed(params: dict[str, Any]) -> FeedParserDict:
    """Get the feed of ArXiv results for a given set of query params.

    Args:
        params: dict[str, Any]: the set of query params to call the ArXiv API.
        See https://info.arxiv.org/help/api/user-manual.html#311-query-interface.

    Returns:
        FeedParserDict: the resulting feed from the ArXiv API call.

    Raises:
        requests.exceptions.HTTPError: when bad requests are made to the API
        ValueError: when the API returns a feed with invalid entries.
    """
    response = requests.get(url=BASE_ARXIV_URL, params=params)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    if not _is_valid_feed(feed):
        raise ValueError(
            f"API call with params:{params} returned a feed with invalid entries"
        )
    return feed


def paginate(
    params: dict[str, Any], max_entries: int, wait_time: int
) -> Iterator[FeedParserDict]:
    """Paginates requests to Arxiv API.

    Args:
        params: dict[str, Any]: the set of query params to call the ArXiv API.
        See https://info.arxiv.org/help/api/user-manual.html#311-query-interface.

        max_entries: int: controls the maximum number of results returned based on the following logic.
        If max_entries = 0, paginates until the total results of the query as given by the API (opensearch_totalresults).
        If max_entries > 0, paginates until at least min(max_results, opensearch_totalresults) have been retrieved.
        The purpose of this parameter is to limit results in non-prod environmets.

        wait_time: int: the number of seconds to wait between ArXiv API calls when paginating.
        According to the terms of use of the API, one should wait at least 3 seconds.

    Yields:
        FeedParserDict: the resulting feed for each page based on the query params.

    """
    if not isinstance(max_entries, int) or max_entries > 1000:
        raise ValueError(
            """Parameter `max_entries` should be an integer lesser than or equal to 1000. 
            See https://info.arxiv.org/help/api/user-manual.html#3112-start-and-max_results-paging.
            """
        )
    if not isinstance(wait_time, int) or wait_time < 3:
        raise ValueError(
            """Parameter `wait_time` should be an integergreater than or equal to 3. 
            See https://info.arxiv.org/help/api/tou.html#rate-limits.
            """
        )
    params = params if params else {}
    params["start"] = 0

    logger.info(f"Searching arXiv with search_query={params.get('search_query', '')}")
    feed = _get_feed(params)
    if max_entries:
        total_results = min(max_entries, int(feed.feed.opensearch_totalresults))
    else:
        total_results = int(feed.feed.opensearch_totalresults)
    total_feeds = total_results // params.get("max_results", 10) + 1
    extracted_feeds = 1
    while params["start"] < total_results:
        logger.info(f"Extracted {extracted_feeds / total_feeds} feeds.")
        yield feed
        params["start"] += params.get("max_results", 10)

        logger.info(f"Waiting for {wait_time} seconds due to ArXiv API terms of use.")
        time.sleep(wait_time)

        feed = _get_feed(params)
