import pytest
from dagster._core.test_utils import environ
from pinkman.utils.environment_helpers import get_dbt_target, get_schema_for_environment


@pytest.mark.parametrize(
    "env_dict,dbt_target",
    [({"DBT_TARGET": "prod"}, "prod"), ({"DBT_TARGET": "ci"}, "ci"), ({}, "dev")],
)
def test_get_dbt_target(env_dict, dbt_target):
    with environ(env_dict):
        assert get_dbt_target() == dbt_target


@pytest.mark.parametrize(
    "env_dict,schema",
    [({"DBT_TARGET": "prod"}, "prod"), ({"DBT_TARGET": "ci"}, "staging"), ({}, "dev")],
)
def test_get_schema_for_env(env_dict, schema):
    with environ(env_dict):
        assert get_schema_for_environment() == schema
