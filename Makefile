uv_install:
	pip install uv

test_install:
	uv pip install -e ".[tests]"

dev_install: uv_install
	uv pip install -e ".[dev]"
	cd pinkman_dbt && dbt deps && cd ..

test_local: test_install
	pytest pinkman_tests -m "not env_bk"  --disable-warnings

manifest:
	cd pinkman_dbt && dbt parse && cd ..

dev:
	dagster dev

lint:
	sqlfluff lint ./pinkman_dbt/models --disable-progress-bar --processes 4

fix:
	sqlfluff fix ./pinkman_dbt/models --disable-progress-bar --processes 4

install_ruff:
	uv pip install ruff

ruff:
	ruff check --fix
	ruff format

update_to_latest_dagster:
	pip freeze | grep '^dagster' | cut -d '=' -f 1 | tr '\n' ' ' | xargs uv pip install --upgrade