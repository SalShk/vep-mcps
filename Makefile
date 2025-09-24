IMAGE=vep-parser-mcp:0.1.1
OUT=parser-mcp/out
IN=tests/data/tiny.vep.tsv
CONS=tests/data/tiny.constraint.tsv

.PHONY: build pipeline test clean

build:
	docker build -t $(IMAGE) -f parser-mcp/Dockerfile .

pipeline: build
	docker run --rm -v "$$(pwd):/wd" -w /wd $(IMAGE) \
	  vep-prepare-pipeline -i $(IN) -c $(CONS) -o $(OUT)

test:
	python -m venv .venv && . .venv/bin/activate && \
	pip install -U pip && pip install -e parser-mcp[dev] && \
	ruff check . && black --check . && pytest -q

clean:
	rm -f $(OUT)/*.tsv
