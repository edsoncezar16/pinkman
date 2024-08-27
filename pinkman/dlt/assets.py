from dagster import (
    AssetExecutionContext,
)
from dagster_embedded_elt.dlt import (
    DagsterDltResource,
    dlt_assets,
)
from pinkman.dlt.sources import arxiv
from pinkman.dlt.destinations import motherduck
from dlt import pipeline


@dlt_assets(
    dlt_source=arxiv(),
    dlt_pipeline=pipeline(
        pipeline_name="arxiv",
        dataset_name="raw",
        destination=motherduck,
        progress="log",
    ),
    name="arxiv",
    group_name="arxiv",
)
def arxiv_assets(context: AssetExecutionContext, dlt: DagsterDltResource):
    yield from dlt.run(context=context)
