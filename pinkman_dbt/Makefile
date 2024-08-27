run:
	dbt run -x

build:
	dbt build -x

test:
	dbt test

SELECT ?= ""
run-local-read-prod:
	dbt compile --target=prod
	mv target prod-target
	dbt run --select $(SELECT) --defer --state prod-target
	rm -rf prod-target