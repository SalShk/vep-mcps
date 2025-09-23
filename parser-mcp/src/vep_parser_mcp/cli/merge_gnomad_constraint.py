from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer
from rich import print

app = typer.Typer()

@app.command()
def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv",
            "-i",
            help="ANNOTATION_NORMALISED input TSV",
            show_default=False,
            metavar="PATH",
        ),
    ],
    constraint_tsv: Annotated[
        Path,
        typer.Option(
            "--constraint-tsv",
            "-c",
            help="gnomAD constraint TSV (.tsv or .tsv.gz)",
            show_default=False,
            metavar="PATH",
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv",
            "-o",
            help="Output merged TSV",
            show_default=False,
            metavar="PATH",
        ),
    ],
    on: Annotated[
        str,
        typer.Option(
            "--on",
            help="Join key: 'gene_symbol' or 'transcript'",
            case_sensitive=False,
        ),
    ] = "gene_symbol",
    how: Annotated[
        str,
        typer.Option(
            "--how",
            help="Join type: 'left' or 'inner'",
            case_sensitive=False,
        ),
    ] = "left",
    constraint_version: Annotated[
        str | None,
        typer.Option(
            "--constraint-version",
            "-v",
            help="Provenance tag (e.g., gnomad-v4.1)",
            show_default=False,
        ),
    ] = None,
) -> None:
    """Merge gnomAD constraint metrics onto annotations on gene_symbol or transcript."""
    try:
        print(f"[debug] Reading input: {in_tsv}, constraint: {constraint_tsv}")
        df = pd.read_csv(in_tsv, sep="\t", dtype=str, low_memory=False)
        cons = pd.read_csv(constraint_tsv, sep="\t", dtype=str, low_memory=False)

        key_map = {"gene_symbol": "Gene_symbol", "transcript": "Transcript"}
        on_key = on.lower().strip()
        if on_key not in key_map:
            raise typer.BadParameter("--on must be 'gene_symbol' or 'transcript'")
        left_key = key_map[on_key]

        if left_key not in df.columns:
            raise ValueError(f"Input TSV missing '{left_key}'")
        if left_key not in cons.columns:
            raise ValueError(f"Constraint TSV missing '{left_key}'")

        cons_renamed = cons.rename(
            columns={c: (f"constraint_{c}" if c != left_key else c) for c in cons.columns}
        )

        how_norm = how.lower().strip()
        if how_norm not in {"left", "inner"}:
            raise typer.BadParameter("--how must be 'left' or 'inner'")

        merged = df.merge(cons_renamed, on=left_key, how=how_norm)
        if constraint_version is not None:
            merged["constraint_version"] = constraint_version

        out_tsv.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(out_tsv, sep="\t", index=False)
        print(f"[green]Merged ({how_norm}) on '{left_key}' → {out_tsv}")
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1) from None

if __name__ == "__main__":
    app()