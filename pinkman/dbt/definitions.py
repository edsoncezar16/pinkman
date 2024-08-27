from dagster import Definitions, load_assets_from_modules
from pinkman.dbt import assets
from pinkman.dbt.resources import dbt_resource


dbt_assets = load_assets_from_modules([assets])


defs = Definitions(
    assets=dbt_assets,
    asset_checks=assets.usage_metrics_daily_freshness_checks,
    resources={
        "dbt": dbt_resource,
    },
)
