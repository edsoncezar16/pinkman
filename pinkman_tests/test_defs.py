import os
import sys
from pathlib import Path
from typing import Callable, Iterator

import pytest
from dagster import (
    AssetsDefinition,
)
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataSet,
    LocalFileCodeReference,
    UrlCodeReference,
)
from dagster._core.test_utils import environ


@pytest.fixture
def reload_pinkman_modules() -> Callable[[], None]:
    def _reload() -> None:
        modules = [*sys.modules.values()]
        for module in modules:
            if "pinkman" in module.__name__:
                sys.modules.pop(module.__name__)

    return _reload


@pytest.fixture
@pytest.mark.parametrize("cloud_env", [True, False])
def prepare_pinkman_environment(
    reload_pinkman_modules: Callable[[], None], cloud_env: bool
) -> Iterator[None]:
    """Sets up the requisite environment to run pinkman."""
    PLACEHOLDER_ENV_VAR_VALUE = "x"
    # Empty values because we don't need to run the pipelines, just load them

    from pinkman.dbt.resources import dbt_resource

    dbt_resource.cli(["deps"]).wait()
    dbt_resource.cli(["parse"], target_path=Path("target")).wait()

    manifest_path = (
        Path(__file__).parent.parent / "pinkman_dbt" / "target" / "manifest.json"
    )

    assert manifest_path.exists()

    if not cloud_env:
        if "DAGSTER_CLOUD_DEPLOYMENT_NAME" in os.environ:
            del os.environ["DAGSTER_CLOUD_DEPLOYMENT_NAME"]
        if "DAGSTER_CLOUD_GIT_URL" in os.environ:
            del os.environ["DAGSTER_CLOUD_GIT_URL"]
        if "DAGSTER_CLOUD_GIT_BRANCH" in os.environ:
            del os.environ["DAGSTER_CLOUD_GIT_BRANCH"]

    with environ(
        {
            "MOTHERDUCK_TOKEN": PLACEHOLDER_ENV_VAR_VALUE,
            "MOTHERDUCK_DATABASE": PLACEHOLDER_ENV_VAR_VALUE,
            **(
                {
                    "DAGSTER_CLOUD_DEPLOYMENT_NAME": "prod",
                    "DAGSTER_CLOUD_GIT_URL": "https://github.com/dagster-io/internal",
                    "DAGSTER_CLOUD_GIT_BRANCH": "master",
                }
                if cloud_env
                else {}
            ),
        }
    ):
        # some pinkman behavior is determined by env vars at import time, so we need to reload the modules
        # between tests
        reload_pinkman_modules()
        yield


@pytest.mark.skip(
    reason="https://dagsterlabs.slack.com/archives/C03DPDM4M0Q/p1721278489574409"
)
@pytest.mark.env_bk
@pytest.mark.parametrize("cloud_env", [True, False])
def test_pinkman_code_location(prepare_pinkman_environment, cloud_env: bool) -> None:
    from pinkman.definitions import defs

    assert len(defs.get_asset_graph().all_asset_keys) > 0
    assert defs.assets is not None

    for asset in defs.assets:
        if not isinstance(asset, AssetsDefinition):
            continue
        for key in asset.keys:
            code_references_meta = CodeReferencesMetadataSet.extract(
                asset.metadata_by_key[key]
            )
            assert code_references_meta.code_references is not None

            assert len(code_references_meta.code_references.code_references) > 0
            is_ref = [
                isinstance(
                    ref, UrlCodeReference if cloud_env else LocalFileCodeReference
                )
                for ref in code_references_meta.code_references.code_references
            ]
            assert all(
                is_ref
            ), f"{key} has incorrect code references: {code_references_meta.code_references.code_references}"
