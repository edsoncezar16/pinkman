import pytest
import duckdb


@pytest.fixture
def duckdb_conn(tmp_path):
    conn = duckdb.connect(f"{tmp_path}/test_data.duckdb")
    yield conn
    conn.close()
