PY ?= python3
export PYTHONPATH := src

.PHONY: help install ingest ingest-fast build check report app test contract all clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## install the package and dev extras
	$(PY) -m pip install -e ".[dev]"

ingest:  ## capture one immutable snapshot (full endpoint sweep, ~2 min)
	$(PY) -m orpulse.cli ingest

ingest-fast:  ## capture usage data only, skipping the per-model endpoint sweep
	$(PY) -m orpulse.cli ingest --no-endpoints

build:  ## rebuild staging and marts from raw, then run quality checks
	$(PY) -m orpulse.cli build

check:  ## run quality checks against the existing marts
	$(PY) -m orpulse.cli check

report:  ## regenerate docs/FINDINGS.md from the marts
	$(PY) -m orpulse.cli report

snapshots:  ## list completed snapshots and their manifests
	$(PY) -m orpulse.cli snapshots

dashboard:  ## build the self-contained HTML dashboard
	$(PY) -m orpulse.cli dashboard

test:  ## unit + quality tests (no network)
	$(PY) -m pytest -q

contract:  ## contract tests against the live API (separate on purpose; may fail loudly)
	$(PY) -m pytest -q -m contract

all: build report dashboard  ## rebuild everything from existing raw snapshots

clean:  ## remove derived data; raw snapshots are never touched
	rm -rf data/staging data/marts
