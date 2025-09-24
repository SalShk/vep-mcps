from __future__ import annotations
import typer
import pandas as pd
from rich.console import Console
from pathlib import Path
import gzip
from typing import Annotated

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
    # Required parameters first
    in_tsv: Annotated[Path, typer.Option("--in-tsv", help="ANNOTATION_NORMALISED input")],
    constraint_tsv: Annotated[Path, typer.Option("--constraint-tsv", help="gnomAD constraint TSV(.gz)")],
    out_tsv: Annotated[Path, typer.Option("--out-tsv")],
    # Optional parameters after required ones
    on: str = typer.Option("gene_symbol", "--on", help="join key: gene_symbol|transcript"),
    how: str = typer.Option("left", "--how", help="left|inner"),
    constraint_version: str = typer.Option(None, "--constraint-version")
) -> None:
    """
    Merge gnomAD constraint metrics onto annotations.
    """
    try:
        with open_read(in_tsv) as f1, open_read(constraint_tsv) as f2:
            ann = pd.read_csv(f1, sep="\t", dtype=str, low_memory=False)
            cons = pd.read_csv(f2, sep="\t", dtype=str, low_memory=False)

        if on == "gene_symbol":
            if "Gene_symbol" not in ann.columns:
                raise ValueError("Annotation missing 'Gene_symbol'. Run normalise step first.")
            key_ann, key_cons = "Gene_symbol", "gene_symbol"
        elif on == "transcript":
            key_ann, key_cons = "Transcript", "transcript"
            if key_ann not in ann.columns:
                raise ValueError("Annotation missing 'Transcript'. Run normalise step first.")
        else:
            raise ValueError("--on must be 'gene_symbol' or 'transcript'.")

        if key_cons not in cons.columns:
            raise ValueError(f"Constraint table missing '{key_cons}'.")

        merged = ann.merge(cons, how=how, left_on=key_ann, right_on=key_cons, suffixes=("", "_constraint"))
        if constraint_version:
            merged["constraint_version"] = constraint_version

        with open_write(out_tsv) as g:
            merged.to_csv(g, sep="\t", index=False)

        console.log(f"[green]Merged ({how}) on {key_ann} → {out_tsv}  (rows: {len(merged)})")
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()