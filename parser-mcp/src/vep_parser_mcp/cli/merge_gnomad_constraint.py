from __future__ import annotations

from typing import Annotated

import pandas as pd
import typer
from rich.console import Console

from ..io.gz import open_read, open_write

app = typer.Typer(add_completion=False)
console = Console()


@app.command(name="run")
def run(
    in_tsv: Annotated[
        str,
        typer.Option(
            ..., "--in-tsv", help="ANNOTATION_NORMALISED input (.tsv/.tsv.gz)"
        ),
    ],
    constraint_tsv: Annotated[
        str,
        typer.Option(
            ..., "--constraint-tsv", help="gnomAD constraint TSV (.tsv/.tsv.gz)"
        ),
    ],
    out_tsv: Annotated[str, typer.Option(..., "--out-tsv", help="Output merged TSV")],
    on: Annotated[
        str,
        typer.Option(
            "gene_symbol", "--on", help="Join key: 'gene_symbol' or 'transcript'"
        ),
    ] = "gene_symbol",
    how: Annotated[
        str, typer.Option("left", "--how", help="Join type: 'left' or 'inner'")
    ] = "left",
    constraint_version: Annotated[
        str | None,
        typer.Option(
            None, "--constraint-version", help="Provenance tag (e.g., gnomad-v4.1)"
        ),
    ] = None,
) -> None:
    """
    Merge gnomAD constraint metrics onto normalised annotations.
    Expects that the normalise step produced 'Gene_symbol' and/or 'Transcript'.
    """
    try:
        how_lc = (how or "left").lower()
        if how_lc not in {"left", "inner"}:
            raise ValueError("--how must be 'left' or 'inner'")

        on_lc = (on or "gene_symbol").lower()
        if on_lc not in {"gene_symbol", "transcript"}:
            raise ValueError("--on must be 'gene_symbol' or 'transcript'")

        with open_read(in_tsv) as f_ann, open_read(constraint_tsv) as f_con:
            ann = pd.read_csv(f_ann, sep="\t", dtype=str, low_memory=False)
            cons = pd.read_csv(f_con, sep="\t", dtype=str, low_memory=False)

        if on_lc == "gene_symbol":
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
            how=how_lc,
            left_on=key_ann,
            right_on=key_cons,
            suffixes=("", "_constraint"),
        )

        if constraint_version:
            merged["constraint_version"] = constraint_version

        with open_write(out_tsv) as g:
            merged.to_csv(g, sep="\t", index=False)

        console.log(
            f"[green]Merged ({how_lc}) on {key_ann} → {out_tsv}  (rows: {len(merged)})"
        )
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
