# VEP MCP Parser

[![Tests](https://img.shields.io/github/actions/workflow/status/salshk/vep-mcps/test.yaml?branch=main)](#)
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
# Commands
**1) vep-filter-consequence-mane**

Filter by consequence (and optionally keep only MANE).

```bash
vep-filter-consequence-mane \
  -i tests/data/tiny.vep.tsv \
  -o parser-mcp/out/filtered.tsv \
  --keep-consequence "missense_variant,stop_gained" \
  --mane-only
```

Input/Output Contract
Accepts: .tsv or .tsv.gz (auto-detected).

Normalised output guarantees:

Gene_symbol (uppercase, or UNKNOWN)

Transcript (string; may be empty)

Constraint file should include:

gene_symbol and/or transcript plus numeric fields (e.g., OE_LOF_UPPER, pLI, …)

See JSON Schemas in ./schemas/:

VEP_RAW.schema.json

ANNOTATION_NORMALISED.schema.json

GNOMAD_CONSTRAINT.schema.json

Makefile Shortcuts
bash
make build         # docker build (vep-parser-mcp:0.1.0)
make test          # run pytest in container
make pipeline      # run one-shot pipeline on tiny fixtures
make overview      # show overview for the merged output
Examples (gz I/O)
bash
vep-prepare-pipeline \
  -i tests/data/tiny.vep.tsv \
  -c tests/data/tiny.constraint.tsv \
  -o parser-mcp/out \
  --gzip-out --skip-overview

# peek
zcat parser-mcp/out/merged.tsv.gz | head
Troubleshooting
"Build repo or workflow not found" badge
Ensure the default branch is master (this repo uses master, not main).

Ensure .github/workflows/test.yaml exists (see example below).

The badge above already points to branch=master.

No overlap on join keys
Check casing/whitespace; merge normalises whitespace and uppercases gene symbols.

Confirm Gene_symbol/Transcript are populated in the normalised file.

Ensure constraint headers include gene_symbol/transcript.

Gene_symbol=UNKNOWN
Use --gene-column SYMBOL if available in the VEP file.

Or provide --tx2gene mapping to backfill from Transcript.

Ragged TSV inputs
Make sure each data row has the same number of columns as header (e.g., awk -F'\t' '{print NR,NF}' file).

Development
bash
# local (without Docker)
uv venv
uv pip install -r parser-mcp/requirements.txt
pip install -e parser-mcp[dev]
pytest -q
ruff check parser-mcp/src tests
black parser-mcp/src tests
Entry points are defined in parser-mcp/pyproject.toml under [project.scripts].

Versioning & Changelog
Tags follow vMAJOR.MINOR.PATCH (e.g., v0.1.0).

See CHANGELOG.md for release notes.

License
MIT — see LICENSE

**Notes**

--keep-consequence accepts comma-separated terms; matches within multi-terms like A&B.

--mane-only keeps rows where MANE_SELECT is truthy (yes/true/1/y/t).

