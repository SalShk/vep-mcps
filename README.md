# VEP MCP Parser

[![Tests](https://img.shields.io/github/actions/workflow/status/salshk/vep-mcps/test.yaml?branch=master)](https://github.com/salshk/vep-mcps/actions/workflows/test.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![Docker](https://img.shields.io/badge/docker-ready-blue)

**VEP MCP Parser** is a compact toolkit of CLI commands (plus a one-shot pipeline) that turns raw **VEP** tabular output into a clean, merged TSV that downstream agents (e.g., *GenoAI Pathogenicity Engine*) can consume immediately.

- **Filter** variants by consequence (and optionally MANE).
- **Normalise** columns to a stable contract (`Gene_symbol`, `Transcript`).
- **Merge** gnomAD constraint metrics by **gene** or **transcript**.
- **Overview** a TSV for quick sanity checks.
- **Pipeline** wrapper to run the whole flow end-to-end.

All commands support **.tsv** and **.tsv.gz** I/O.

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


