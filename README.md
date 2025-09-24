# VEP MCP Parser

[![Tests](https://img.shields.io/github/actions/workflow/status/SalShk/vep-mcps/test.yaml?branch=master)](https://github.com/SalShk/vep-mcps/actions/workflows/test.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![Docker](https://img.shields.io/badge/docker-ready-blue)

**VEP MCP Parser** is a compact toolkit that turns raw **VEP** TSVs into a clean, merged table ready for downstream agents (e.g. *GenoAI Pathogenicity Engine*).

- **Filter** by consequence (optional MANE / CANONICAL)
- **Normalise** to stable keys: `Gene_symbol`, `Transcript`
- **Merge** gnomAD constraint (by gene or transcript)
- **Overview** quick sanity checks
- **Pipeline** one-shot: filter → normalise → merge → overview  
_All commands support `.tsv` and `.tsv.gz`._

---

## Install & Quickstart

### Docker (recommended)

```bash
# from repo root
docker build -t vep-parser-mcp:0.1.0 -f parser-mcp/Dockerfile .

# run end-to-end on tiny fixtures
docker run --rm -v "$PWD:/wd" -w /wd vep-parser-mcp:0.1.0 \
  vep-prepare-pipeline \
  -i tests/data/tiny.vep.tsv \
  -c tests/data/tiny.constraint.tsv \
  -o parser-mcp/out
```

# Python (editable dev)

```bash
uv venv
uv pip install -r parser-mcp/requirements.txt
pip install -e parser-mcp[dev]
pytest -q
```

# CLI Cheat-Sheet

```bash
# 1) Filter
vep-filter-consequence-mane \
  -i input.vep.tsv[.gz] \
  -o out/filtered.tsv[.gz] \
  --keep-consequence "missense_variant,stop_gained" \
  --mane-only --require-canonical

# 2) Normalise
vep-normalise-columns \
  -i out/filtered.tsv[.gz] \
  -o out/normalised.tsv[.gz] \
  --vep-cache-version 109 --plugins-version v1.0 \
  --gene-column SYMBOL  # if present

# 3) Merge gnomAD constraint
vep-merge-gnomad-constraint \
  -i out/normalised.tsv[.gz] \
  -c gnomad.constraint.tsv[.gz] \
  -o out/merged.tsv[.gz] \
  --on transcript --how left

# 4) Overview
vep-parsing-overview -i out/merged.tsv[.gz]
```
# Makefile Shortcuts

```bash
make build     # docker build (vep-parser-mcp:0.1.0)
make test      # run pytest in container
make pipeline  # run one-shot pipeline on tiny fixtures
make overview  # show overview for the merged output
```

