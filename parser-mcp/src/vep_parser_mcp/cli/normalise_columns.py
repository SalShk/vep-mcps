from __future__ import annotations

from typing import Annotated

import pandas as pd
import typer
from rich.console import Console

from ..io.gz import open_read, open_write

app = typer.Typer(add_completion=False)
console = Console()

# Map VEP columns to normalized names expected downstream
RENAME_MAP = {
    "Feature": "Transcript",
    "SYMBOL": "Gene_symbol",
}

# Numeric plugin/annotation fields to coerce when present
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


@app.command(name="run")
def run(
    in_tsv: Annotated[
        str, typer.Option(..., "--in-tsv", help="Input VEP TSV (.tsv or .tsv.gz)")
    ],
    out_tsv: Annotated[
        str, typer.Option(..., "--out-tsv", help="Output normalized TSV")
    ],
    vep_cache_version: Annotated[
        str | None, typer.Option(None, "--vep-cache-version", help="Provenance tag")
    ] = None,
    plugins_version: Annotated[
        str | None, typer.Option(None, "--plugins-version", help="Provenance tag")
    ] = None,
) -> None:
    """
    Normalize column names and coerce selected fields to numeric where applicable.
    Adds optional provenance fields (vep_cache_version, plugins_version).
    """
    try:
        with open_read(in_tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

        if df.empty:
            console.log(
                "[yellow]Input file has no rows; writing empty output unchanged."
            )

        # Rename standard columns (only if present)
        present = {old: new for old, new in RENAME_MAP.items() if old in df.columns}
        if present:
            df = df.rename(columns=present)

        # Coerce numeric plugin fields when present
        for col in NUMERIC_FIELDS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Add provenance tags
        if vep_cache_version:
            df["vep_cache_version"] = vep_cache_version
        if plugins_version:
            df["plugins_version"] = plugins_version

        with open_write(out_tsv) as g:
            df.to_csv(g, sep="\t", index=False)

        console.log(
            f"[green]Normalised → {out_tsv}  (rows: {len(df)}, cols: {len(df.columns)})"
        )
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
