"""Ingestion via `dlt`."""

from dagster import Definitions, load_assets_from_modules
from dagster_embedded_elt.dlt import DagsterDltResource
from pinkman.dlt import assets


defs = Definitions(
    assets=load_assets_from_modules([assets]),
    resources={
        "dlt": DagsterDltResource(),
    },
)
