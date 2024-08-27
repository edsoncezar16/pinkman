"""Arxiv API ingestion with `dlt`.

EXAMPLE USAGE

    This script can be run both locally, and through a Dagster materialization. To run
    the script locally, perform the following:

        export $(xargs <.env)  # source environment variables in `.env`

        python pinkman/dlt/sources/arxiv/main.py

"""

import dlt
import logging
from pinkman.utils.arxiv_helpers import paginate
from pinkman.dlt.sources.arxiv.settings import (
    QUERIES,
    ENTRIES_PER_PAGE,
    WAIT_TIME,
    BASE_ARXIV_URL,
    MAX_ENTRIES,
)
from pinkman.dlt.destinations import motherduck
from pinkman.utils.environment_helpers import get_schema_for_environment

logger = logging.getLogger(__name__)


@dlt.source(max_table_nesting=0)
def arxiv(
    queries: list[str],
    entries_per_page: int = ENTRIES_PER_PAGE,
    max_entries: int = MAX_ENTRIES,
    wait_time: int = WAIT_TIME,
):
    if not isinstance(entries_per_page, int) or entries_per_page > 1000:
        raise ValueError(
            """Parameter `entries_per_page` should be an integer lesser than or equal to 1000.
                         See https://info.arxiv.org/help/api/user-manual.html#3112-start-and-max_results-paging"""
        )

    @dlt.resource(primary_key="id", write_disposition="merge")
    def feeds():
        for query in queries:
            params = {
                "search_query": f'ti:"{query}"+OR+abs:"{query}"',
                "max_results": entries_per_page,
            }
            yield from (
                feed.feed
                for feed in paginate(BASE_ARXIV_URL, params, max_entries, wait_time)
            )

    @dlt.transformer(primary_key="id", write_disposition="merge", data_from=feeds)
    def entries(feeds):
        for feed in feeds:
            for entry in feed.entries:
                yield entry

    return feeds, entries


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    schema = get_schema_for_environment()

    pipeline = dlt.pipeline(
        pipeline_name="arxiv",
        destination=motherduck,
        dataset_name=schema,
    )
    load_info = pipeline.run(arxiv(queries=QUERIES, max_entries=MAX_ENTRIES))
    logger.info(load_info)
