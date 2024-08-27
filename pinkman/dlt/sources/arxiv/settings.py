"""ArXiv source settings and constants."""

from pinkman.utils.environment_helpers import get_dbt_target

BASE_ARXIV_URL = "http://export.arxiv.org/api/query"

ARXIV_TIMEZONE = "America/Manaus"

QUERIES = [
    "quantum computing",
    "data science",
    "data engineering",
    "superconductivity",
    "quantum vacuum",
    "astronomy",
    "reinforcement learning",
    "generative AI",
    "data governance",
    "data quality",
]

ENTRIES_PER_PAGE = 1000

MAX_ENTRIES = 0 if get_dbt_target() == "prod" else 10000

WAIT_TIME = 3
