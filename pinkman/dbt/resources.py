from pathlib import Path

from dagster_dbt import DbtCliResource, DbtProject
from pinkman.utils.environment_helpers import get_dbt_target

pinkman_dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..", "pinkman_dbt").resolve(),
    target=get_dbt_target(),
)

dbt_resource = DbtCliResource(project_dir=pinkman_dbt_project)
