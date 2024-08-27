import warnings
import pinkman.dbt.definitions as dbt_definitions
import pinkman.dlt.definitions as dlt_definitions
from dagster import Definitions
from dagster import ExperimentalWarning

warnings.filterwarnings("ignore", category=ExperimentalWarning)


defs = Definitions.merge(
    dbt_definitions.defs,
    dlt_definitions.defs,
)
