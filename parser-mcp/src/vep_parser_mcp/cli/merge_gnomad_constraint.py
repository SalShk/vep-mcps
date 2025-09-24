from __future__ import annotations
from pathlib import Path
from typing import Annotated
import gzip
import pandas as pd
import typer
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

def open_read(path: Path):
    if str(path).endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')
    return open(path, 'r', encoding='utf-8')

def open_write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if str(path).endswith('.gz'):
        return gzip.open(path, 'wt', encoding='utf-8')
    return open(path, 'w', encoding='utf-8')

@app.command()
def main(
    in_tsv: Annotated[Path, typer.Option("--in-tsv", "-i", help="ANNOTATION_NORMALISED input", exists=True, readable=True)],
    constraint_tsv: Annotated[Path, typer.Option("--constraint-tsv", "-c", help="gnomAD constraint TSV(.gz)", exists=True, readable=True)],
    out_tsv: Annotated[Path, typer.Option("--out-tsv", "-o", help="Output TSV")],
    on: Annotated[str, typer.Option("--on", help="join key: gene_symbol|transcript")] = "gene_symbol",
    how: Annotated[str, typer.Option("--how", help="left|inner")] = "left",
    constraint_version: Annotated[str | None, typer.Option("--constraint-version")] = None,
) -> None:
    """
    Merge gnomAD constraint metrics onto annotations.
    """
    try:
        with open_read(in_tsv) as f1, open_read(constraint_tsv) as f2:
            ann = pd.read_csv(f1, sep="\t", dtype=str, low_memory=False).fillna("")
            cons = pd.read_csv(f2, sep="\t", dtype=str, low_memory=False).fillna("")

        if on not in {"gene_symbol", "transcript"}:
            raise typer.BadParameter("--on must be 'gene_symbol' or 'transcript'")

        # determine left/right key columns
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

        # normalize keys: strip + case (genes uppercase; transcripts left as-is)
        ann[left_key] = ann[left_key].astype(str).str.strip()
        cons[right_key] = cons[right_key].astype(str).str.strip()
        if on == "gene_symbol":
            ann[left_key] = ann[left_key].str.upper()
            cons[right_key] = cons[right_key].str.upper()

        # helpful diagnostics
        left_vals  = set(ann[left_key].unique()) - {""}
        right_vals = set(cons[right_key].unique()) - {""}
        overlap = left_vals & right_vals
        console.log(f"[blue]Join on '{on}': left uniques={len(left_vals)}, right uniques={len(right_vals)}, overlap={len(overlap)}")
        if not overlap:
            console.log("[yellow]WARNING: no overlapping join keys; proceeding with merge anyway (will yield NaNs).")

        merged = ann.merge(cons, how=how, left_on=left_key, right_on=right_key, suffixes=("", "_constraint"))
        if constraint_version:
            merged["constraint_version"] = constraint_version

        with open_write(out_tsv) as g:
            merged.to_csv(g, sep="\t", index=False)

        console.log(f"[green]Merged ({how}) on {left_key} → {out_tsv}  (rows: {len(merged)})")
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
