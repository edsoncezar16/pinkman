"""Customize Env Vars config for dlt destinations."""

import os

from dlt.destinations import motherduck

md_credentials = {
    "database": os.getenv("MOTHERDUCK_DATABASE"),
    "password": os.getenv("MOTHERDUCK_TOKEN"),
}

md_destination = motherduck(credentials=md_credentials)
