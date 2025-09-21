from __future__ import annotations

import pandas as pd
import typer
from rich.console import Console

from ..io.gz import open_read, open_write

app = typer.Typer(add_completion=False)
console = Console()

RENAME_MAP = {
    "Feature": "Transcript",
    "SYMBOL": "Gene_symbol",
}

NUMERIC_FIELDS = [
    "REVEL_score",
    "CADD_PHRED",
    "dbNSFP_GERP",
    "dbNSFP_phyloP",
    "dbNSFP_phastCons",
    "SpliceAI_DS_AG",
    "SpliceAI_DS_AL",
    "SpliceAI_DS_DG",
    "SpliceAI_DS_DL",
]


@app.command()
def main(
    in_tsv: str = typer.Option(..., "--in-tsv", help="Input TSV (VEP_RAW or filtered)"),
    out_tsv: str = typer.Option(
        ..., "--out-tsv", help="Output TSV (ANNOTATION_NORMALISED)"
    ),
    vep_cache_version: str | None = typer.Option(
        None, "--vep-cache-version", help="Optional VEP cache version"
    ),
    plugins_version: str | None = typer.Option(
        None, "--plugins-version", help="Optional plugin bundle version"
    ),
) -> None:
    """
    Normalise column names and coerce plugin fields to numeric where applicable.
    Adds optional provenance fields.
    """
    try:
        with open_read(in_tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

        # Rename standard columns
        for old, new in RENAME_MAP.items():
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)

        # Coerce numeric plugin fields if present
        for col in NUMERIC_FIELDS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Provenance
        if vep_cache_version:
            df["vep_cache_version"] = vep_cache_version
        if plugins_version:
            df["plugins_version"] = plugins_version

        with open_write(out_tsv) as g:
            df.to_csv(g, sep="\t", index=False)

        console.log(f"[green]Normalised → {out_tsv}")
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1) from e
