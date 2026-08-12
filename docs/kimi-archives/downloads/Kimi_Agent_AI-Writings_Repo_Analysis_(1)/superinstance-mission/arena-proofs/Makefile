ZARENA_DIR ?= /mnt/agents/repos/zeroclaw-arena

.PHONY: data test report install

install:
	pip install -e .

data:
	ZARENA_DIR=$(ZARENA_DIR) bash scripts/fetch_data.sh

test:
	python3 -m pytest -q

report:
	python3 -m arena_proofs
