import datetime
import json
from typing import Any, Mapping, Optional

from dagster import (
    AssetExecutionContext,
    AssetKey,
    BackfillPolicy,
    Config,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.last_update import (
    build_last_update_freshness_checks,
)
from dagster_dbt import (
    DagsterDbtTranslator,
    DagsterDbtTranslatorSettings,
    DbtCliResource,
    dbt_assets,
)
from dagster_dbt.asset_utils import get_asset_key_for_model
from pinkman.dbt.resources import pinkman_dbt_project

INCREMENTAL_SELECTOR = "config.materialized:incremental"
SNAPSHOT_SELECTOR = "resource_type:snapshot"


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        if dbt_resource_props["resource_type"] == "snapshot":
            return "snapshots"
        # Same logic that sets the custom schema in macros/get_custom_schema.sql
        asset_path = dbt_resource_props["fqn"][1:-1]
        if asset_path:
            return "_".join(asset_path)
        return "default"

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        resource_database = dbt_resource_props["database"]
        resource_schema = dbt_resource_props["schema"]
        resource_name = dbt_resource_props["name"]
        resource_type = dbt_resource_props["resource_type"]

        # if metadata has been provided in the yaml use that, otherwise construct key
        if (
            resource_type == "source"
            and "meta" in dbt_resource_props
            and "dagster" in dbt_resource_props["meta"]
            and "asset_key" in dbt_resource_props["meta"]["dagster"]
        ):
            return AssetKey(dbt_resource_props["meta"]["dagster"]["asset_key"])

        return AssetKey([resource_database, resource_schema, resource_name])


@dbt_assets(
    manifest=pinkman_dbt_project.manifest_path,
    dagster_dbt_translator=CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_code_references=True)
    ),
    exclude=INCREMENTAL_SELECTOR + " " + SNAPSHOT_SELECTOR,
    backfill_policy=BackfillPolicy.single_run(),
    project=pinkman_dbt_project,
)
def dbt_non_partitioned_models(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from (
        dbt.cli(["build"], context=context)
        .stream()
        .fetch_row_counts()
        .fetch_column_metadata()
    )


class DbtConfig(Config):
    full_refresh: bool = False


@dbt_assets(
    manifest=pinkman_dbt_project.manifest_path,
    select=INCREMENTAL_SELECTOR,
    dagster_dbt_translator=CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_code_references=True)
    ),
    backfill_policy=BackfillPolicy.single_run(),
    project=pinkman_dbt_project,
)
def dbt_partitioned_models(
    context: AssetExecutionContext, dbt: DbtCliResource, config: DbtConfig
):
    dbt_vars = {
        "min_date": context.partition_time_window.start.isoformat(),
        "max_date": context.partition_time_window.end.isoformat(),
    }
    args = ["build", "--vars", json.dumps(dbt_vars)]

    if config.full_refresh:
        args = ["build", "--full-refresh"]

    yield from (
        dbt.cli(args, context=context)
        .stream()
        .fetch_row_counts()
        .fetch_column_metadata()
    )


@dbt_assets(
    manifest=pinkman_dbt_project.manifest_path,
    select=SNAPSHOT_SELECTOR,
    dagster_dbt_translator=CustomDagsterDbtTranslator(
        settings=DagsterDbtTranslatorSettings(enable_code_references=True)
    ),
    backfill_policy=BackfillPolicy.single_run(),
    project=pinkman_dbt_project,
)
def dbt_snapshot_models(
    context: AssetExecutionContext, dbt: DbtCliResource, config: DbtConfig
):
    yield from dbt.cli(["snapshot"], context=context).stream().with_insights()


# Usage metrics daily gets materialized each day. Give at least 12 hours berth time for any easy problems to be resolved.
usage_metrics_daily_freshness_checks = build_last_update_freshness_checks(
    assets=[
        get_asset_key_for_model([dbt_non_partitioned_models], "usage_metrics_daily"),
        get_asset_key_for_model(
            [dbt_partitioned_models], "usage_metrics_daily_jobs_aggregated"
        ),
    ],
    lower_bound_delta=datetime.timedelta(hours=36),
)
