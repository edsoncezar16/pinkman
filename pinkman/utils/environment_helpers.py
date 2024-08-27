import os


def get_dbt_target() -> str:
    return os.getenv("DBT_TARGET", "dev")


def get_schema_for_environment() -> str:
    """Returns the schema to use in the current environment."""
    env = get_dbt_target()
    match env:
        case "prod":
            return "prod"
        case "ci":
            return "staging"
        case _:
            return "dev"
