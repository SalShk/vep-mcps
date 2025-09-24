from __future__ import annotations

from pathlib import Path
from typing import Annotated
import os
import sys
import gzip
import re

import pandas as pd
import typer
from rich import print

app = typer.Typer(add_completion=False)

# e.g. "NM_000001.1:c.100A>G" → "NM_000001.1"
NM_RE = re.compile(r"\b(NM_\d+(?:\.\d+)?)")

# ---------------- I/O helpers: stdin/stdout + .gz ----------------
def _open_read_any(path: Path | str):
    p = str(path)
    if p == "-" or p == "":
        return sys.stdin
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "r", encoding="utf-8")

def _open_write_any(path: Path | str):
    p = str(path)
    if p == "-" or p == "":
        return sys.stdout
    os.makedirs(str(Path(p).parent), exist_ok=True)
    if p.endswith(".gz"):
        return gzip.open(p, "wt", encoding="utf-8")
    return open(p, "w", encoding="utf-8")

# ---------------- small helpers ----------------
def infer_transcript_from_hgvs(hgvs: str | None) -> str | None:
    if hgvs is None or str(hgvs).strip() == "":
        return None
    m = NM_RE.search(str(hgvs))
    return m.group(1) if m else None

def load_tx2gene_map(path: str | None) -> dict[str, str]:
    """Load a simple TSV with columns: Transcript, Gene_symbol"""
    if not path:
        return {}
    df = pd.read_table(path, dtype=str).fillna("")
    for c in ("Transcript", "Gene_symbol"):
        if c not in df.columns:
            raise ValueError("tx2gene file must have columns: Transcript, Gene_symbol")
    df["Transcript"] = df["Transcript"].astype(str).str.strip()
    df["Gene_symbol"] = df["Gene_symbol"].astype(str).str.upper().str.strip()
    return dict(zip(df["Transcript"], df["Gene_symbol"]))

@app.command()
def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv", "-i",
            help="Input TSV file from VEP (post-filter). Use '-' for stdin.",
            exists=False,   # allow '-'
            readable=True,
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv", "-o",
            help="Output TSV with normalised columns. Use '-' for stdout.",
            writable=True,
        ),
    ],
    vep_cache_version: Annotated[str | None, typer.Option("--vep-cache-version")] = None,
    plugins_version: Annotated[str | None, typer.Option("--plugins-version")] = None,
    gene_column: Annotated[
        str | None,
        typer.Option(
            "--gene-column",
            help="Use this source column as Gene_symbol (e.g., SYMBOL).",
        ),
    ] = None,
    tx2gene: Annotated[
        str | None,
        typer.Option(
            "--tx2gene",
            help="Optional transcript→gene map TSV with columns: Transcript, Gene_symbol.",
        ),
    ] = None,
) -> None:
    """Normalise VEP TSV columns and populate Gene_symbol/Transcript when possible."""
    try:
        print(f"[debug] Reading input: {in_tsv}")
        with _open_read_any(in_tsv) as fin:
            df = pd.read_csv(fin, sep="\t", dtype=str, low_memory=False).fillna("")

        print(f"[debug] Original columns: {list(df.columns)}")

        # Canonical renames (apply only if present)
        column_mapping = {
            # Gene symbol synonyms → Gene_symbol
            "SYMBOL": "Gene_symbol",
            "Gene": "Gene_symbol",
            "Gene_name": "Gene_symbol",
            "symbol": "Gene_symbol",
            "GENE_PHENO": "Gene_pheno",  # keep original info for reference

            # Transcript synonyms → Transcript
            "Feature": "Transcript",
            "feature": "Transcript",
            "Feature_type": "Transcript",
            "Transcript_ID": "Transcript",
            "transcript_id": "Transcript",

            # dbSNP synonyms → dbSNP
            "Existing_variation": "dbSNP",
            "RSID": "dbSNP",
            "dbsnp": "dbSNP",
            "rs_dbSNP": "dbSNP",

            # MANE variants → MANE_SELECT (normalize name)
            "MANE_select": "MANE_SELECT",
            "mane_select": "MANE_SELECT",
            "MANE": "MANE_SELECT",
        }

        mapping_to_apply = {k: v for k, v in column_mapping.items() if k in df.columns}
        if mapping_to_apply:
            df = df.rename(columns=mapping_to_apply)
            print(f"[debug] Applied column mappings: {mapping_to_apply}")
        else:
            print("[debug] No column mappings applied.")

        # Ensure canonical columns exist
        if "Gene_symbol" not in df.columns:
            df["Gene_symbol"] = ""
        if "Transcript" not in df.columns:
            df["Transcript"] = ""

        # If user provided a specific gene column, use it (only where non-empty)
        if gene_column and gene_column in df.columns:
            src = df[gene_column].astype(str)
            df.loc[src.str.strip() != "", "Gene_symbol"] = src

        # Infer Transcript from clinvar_hgvs if we still don't have any
        if (df["Transcript"].str.strip() == "").all() and "clinvar_hgvs" in df.columns:
            df["Transcript"] = df["clinvar_hgvs"].apply(infer_transcript_from_hgvs).fillna("")

        # If Gene_symbol still empty, try transcript→gene map
        tx2gene_map = load_tx2gene_map(tx2gene)
        if tx2gene_map and (df["Gene_symbol"].str.strip() == "").any():
            mask = df["Gene_symbol"].str.strip() == ""
            df.loc[mask, "Gene_symbol"] = df.loc[mask, "Transcript"].map(tx2gene_map).fillna("")

        # Final standardisation
        df["Gene_symbol"] = (
            df["Gene_symbol"].astype(str).str.upper().str.strip().replace({"": "UNKNOWN"})
        )
        df["Transcript"] = df["Transcript"].astype(str).str.strip()

        # Add metadata if provided
        if vep_cache_version:
            df["vep_cache_version"] = vep_cache_version
        if plugins_version:
            df["plugins_version"] = plugins_version

        # Keep key columns handy near the front (do not reorder everything else)
        front = [c for c in ["variant_id", "Gene_symbol", "Transcript"] if c in df.columns]
        others = [c for c in df.columns if c not in front]
        df = df[front + others]

        # Write out
        with _open_write_any(out_tsv) as fout:
            df.to_csv(fout, sep="\t", index=False)

        print(f"[green]Normalized columns and wrote {out_tsv} (rows: {len(df)})")
        unk = int((df["Gene_symbol"] == "UNKNOWN").sum())
        if unk:
            print(
                "[yellow][normalise] WARNING: "
                f"{unk} rows have Gene_symbol=UNKNOWN. "
                "Provide --gene-column SYMBOL or a --tx2gene map for gene-level merge."
            )

    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    # Support BOTH:
    #   - python -m vep_parser_mcp.cli.X --flags ...
    #   - python -m vep_parser_mcp.cli.X main --flags ...
    # If the first arg looks like a flag, treat it as a single-command app.
    import sys
    first = sys.argv[1] if len(sys.argv) > 1 else ""
    if first.startswith("-"):
        import typer
        typer.run(main)   # single-command style
    else:
        app()             # subcommand style (expects "main" or other subcommands)
