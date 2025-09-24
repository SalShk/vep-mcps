from __future__ import annotations
from pathlib import Path
from typing import Annotated
import os
import sys
import gzip

import pandas as pd
import typer
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

# ---------- I/O helpers: stdin/stdout + .gz ----------
def open_read_any(path: Path | str):
    p = str(path)
    if p == "-" or p == "":
        return sys.stdin
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "r", encoding="utf-8")

def open_write_any(path: Path | str):
    p = str(path)
    if p == "-" or p == "":
        return sys.stdout
    os.makedirs(str(Path(p).parent), exist_ok=True)
    if p.endswith(".gz"):
        return gzip.open(p, "wt", encoding="utf-8")
    return open(p, "w", encoding="utf-8")

@app.command()
def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv", "-i",
            help="ANNOTATION_NORMALISED input (use '-' for stdin)",
            exists=False,  # allow '-'
            readable=True,
        ),
    ],
    constraint_tsv: Annotated[
        Path,
        typer.Option(
            "--constraint-tsv", "-c",
            help="gnomAD constraint TSV(.gz) (use '-' for stdin)",
            exists=False,  # allow '-'
            readable=True,
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv", "-o",
            help="Output TSV (use '-' for stdout)",
            writable=True,
        ),
    ],
    on: Annotated[str, typer.Option("--on", help="join key: gene_symbol|transcript")] = "gene_symbol",
    how: Annotated[str, typer.Option("--how", help="left|inner")] = "left",
    constraint_version: Annotated[str | None, typer.Option("--constraint-version")] = None,
) -> None:
    """
    Merge gnomAD constraint metrics onto annotations.
    """
    try:
        on = on.strip().lower()
        if on not in {"gene_symbol", "transcript"}:
            raise typer.BadParameter("--on must be 'gene_symbol' or 'transcript'")

        how = how.strip().lower()
        if how not in {"left", "inner"}:
            raise typer.BadParameter("--how must be 'left' or 'inner'")

        # Read inputs
        with open_read_any(in_tsv) as f1:
            ann = pd.read_csv(f1, sep="\t", dtype=str, low_memory=False).fillna("")
        with open_read_any(constraint_tsv) as f2:
            cons = pd.read_csv(f2, sep="\t", dtype=str, low_memory=False).fillna("")

        # Determine left/right keys
        ann_gene_col = "Gene_symbol" if "Gene_symbol" in ann.columns else None
        ann_tx_col   = "Transcript"  if "Transcript"  in ann.columns else None

        if on == "gene_symbol":
            if not ann_gene_col:
                console.log("[red]Annotation missing 'Gene_symbol'. Run normalise step first.")
                raise typer.Exit(code=1)
            left_key, right_key = ann_gene_col, "gene_symbol"
        else:
            if not ann_tx_col:
                console.log("[red]Annotation missing 'Transcript'. Run normalise step first.")
                raise typer.Exit(code=1)
            left_key, right_key = ann_tx_col, "transcript"

        if right_key not in cons.columns:
            console.log(f"[red]Constraint table missing '{right_key}'.")
            raise typer.Exit(code=1)

        # Normalise keys
        ann[left_key]  = ann[left_key].astype(str).str.strip()
        cons[right_key]= cons[right_key].astype(str).str.strip()
        if on == "gene_symbol":
            ann[left_key]   = ann[left_key].str.upper()
            cons[right_key] = cons[right_key].str.upper()

        # Diagnostics
        left_vals  = set(ann[left_key].unique()) - {""}
        right_vals = set(cons[right_key].unique()) - {""}
        overlap = left_vals & right_vals
        console.log(f"[blue]Join on '{on}': left uniques={len(left_vals)}, right uniques={len(right_vals)}, overlap={len(overlap)}")
        if not overlap:
            console.log("[yellow]WARNING: no overlapping join keys; proceeding (will yield empty/NaN constraint columns).")

        # Merge
        merged = ann.merge(
            cons,
            how=how,
            left_on=left_key,
            right_on=right_key,
            suffixes=("", "_constraint"),
        )

        if constraint_version:
            merged["constraint_version"] = constraint_version

        # Write output
        with open_write_any(out_tsv) as g:
            merged.to_csv(g, sep="\t", index=False)

        console.log(f"[green]Merged ({how}) on {left_key} → {out_tsv}  (rows: {len(merged)})")

    except typer.Exit:
        raise
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    import typer
    typer.run(main)