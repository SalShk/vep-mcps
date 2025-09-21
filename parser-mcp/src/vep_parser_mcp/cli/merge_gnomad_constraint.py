from __future__ import annotations

import pandas as pd
import typer
from rich.console import Console

from ..io.gz import open_read, open_write

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    in_tsv: str = typer.Option(..., "--in-tsv", help="ANNOTATION_NORMALISED input TSV"),
    constraint_tsv: str = typer.Option(
        ..., "--constraint-tsv", help="gnomAD constraint TSV (.tsv or .tsv.gz)"
    ),
    on: str = typer.Option(
        "gene_symbol", "--on", help="Join key: 'gene_symbol' or 'transcript'"
    ),
    how: str = typer.Option("left", "--how", help="Join type: 'left' or 'inner'"),
    out_tsv: str = typer.Option(..., "--out-tsv", help="Output merged TSV"),
    constraint_version: str | None = typer.Option(
        None, "--constraint-version", help="Optional provenance tag (e.g., gnomad-v4.1)"
    ),
) -> None:
    """
    Merge gnomAD constraint metrics onto normalised annotations.
    """
    try:
        with open_read(in_tsv) as f1, open_read(constraint_tsv) as f2:
            ann = pd.read_csv(f1, sep="\t", dtype=str, low_memory=False)
            cons = pd.read_csv(f2, sep="\t", dtype=str, low_memory=False)

        if on not in {"gene_symbol", "transcript"}:
            raise ValueError("--on must be 'gene_symbol' or 'transcript'.")

        if on == "gene_symbol":
            key_ann, key_cons = "Gene_symbol", "gene_symbol"
            if key_ann not in ann.columns:
                raise ValueError(
                    "Annotation missing 'Gene_symbol'. Run normalise step first."
                )
        else:
            key_ann, key_cons = "Transcript", "transcript"
            if key_ann not in ann.columns:
                raise ValueError(
                    "Annotation missing 'Transcript'. Run normalise step first."
                )

        if key_cons not in cons.columns:
            raise ValueError(f"Constraint table missing '{key_cons}'.")

        merged = ann.merge(
            cons,
            how=how,
            left_on=key_ann,
            right_on=key_cons,
            suffixes=("", "_constraint"),
        )

        if constraint_version:
            merged["constraint_version"] = constraint_version

        with open_write(out_tsv) as g:
            merged.to_csv(g, sep="\t", index=False)

        console.log(
            f"[green]Merged ({how}) on {key_ann} → {out_tsv}  (rows: {len(merged)})"
        )
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1) from e
