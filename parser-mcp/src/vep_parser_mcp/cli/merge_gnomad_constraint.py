from __future__ import annotations
import typer
import pandas as pd
from rich.console import Console
from ..io.gz import open_read, open_write

app = typer.Typer(add_completion=False)
console = Console()

@app.command()
def app(
    in_tsv: str = typer.Option(..., "--in-tsv", help="ANNOTATION_NORMALISED input"),
    constraint_tsv: str = typer.Option(..., "--constraint-tsv", help="gnomAD constraint TSV(.gz)"),
    on: str = typer.Option("gene_symbol", "--on", help="join key: gene_symbol|transcript"),
    how: str = typer.Option("left", "--how", help="left|inner"),
    out_tsv: str = typer.Option(..., "--out-tsv"),
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
