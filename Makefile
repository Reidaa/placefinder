CSV_FILE = kebabs.csv
SQLITE_FILE = kebabs.sqlite3

.PHONY: setup
setup:
	uv sync

.PHONY: run
run: check
	uv run -m placefinder

.PHONY: check
check:
	uv run mypy -p placefinder

.PHONY: format
format:
	uv run ruff check --select I --fix
	uv run ruff format

.PHONY: fmt
fmt: format

.PHONY: lint
lint:
	uv run ruff check
