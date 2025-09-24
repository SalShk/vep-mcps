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
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")

def open_write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if str(path).endswith(".gz"):
        return gzip.open(path, "wt", encoding="utf-8")
    return open(path, "w", encoding="utf-8")

@app.command()
def main(
    in_tsv: Annotated[Path, typer.Option("--in-tsv", "-i", help="ANNOTATION_NORMALISED input")],
    constraint_tsv: Annotated[Path, typer.Option("--constraint-tsv", "-c", help="gnomAD constraint TSV(.gz)")],
    out_tsv: Annotated[Path, typer.Option("--out-tsv", "-o")],
    on: str = typer.Option("gene_symbol", "--on", help="join key: gene_symbol|transcript"),
    how: str = typer.Option("left", "--how", help="left|inner"),
    constraint_version: str | None = typer.Option(None, "--constraint-version"),
) -> None:
    """
    Merge gnomAD constraint metrics onto annotations.
    """
    try:
        with open_read(in_tsv) as f1, open_read(constraint_tsv) as f2:
            ann = pd.read_csv(f1, sep="\t", dtype=str, low_memory=False).fillna("")
            cons = pd.read_csv(f2, sep="\t", dtype=str, low_memory=False).fillna("")

        # Normalise header variants on both sides
        ann = ann.rename(columns={
            "SYMBOL":"Gene_symbol","Gene":"Gene_symbol","symbol":"Gene_symbol",
            "Feature":"Transcript","feature":"Transcript","Transcript_ID":"Transcript","transcript_id":"Transcript",
        })
        cons = cons.rename(columns={
            "SYMBOL":"Gene_symbol","Gene":"Gene_symbol","gene":"Gene_symbol","symbol":"Gene_symbol",
            "Feature":"Transcript","feature":"Transcript","Transcript_ID":"Transcript","transcript_id":"Transcript",
        })

        # Decide the join key
        key_ann: str | None = None
        key_cons: str | None = None
        on_norm = (on or "").lower().strip()

        if on_norm in {"gene_symbol","genesymbol"}:
            if "Gene_symbol" not in ann.columns:
                raise ValueError("Annotation missing 'Gene_symbol'. Run normalise step first.")
            key_ann = "Gene_symbol"; key_cons = "Gene_symbol"
        elif on_norm == "transcript":
            if "Transcript" not in ann.columns:
                raise ValueError("Annotation missing 'Transcript'. Run normalise step first.")
            key_ann = "Transcript"; key_cons = "Transcript"
        else:
            for k in ("Gene_symbol","Transcript"):
                if k in ann.columns and k in cons.columns and ann[k].str.strip().ne("").any():
                    key_ann = key_cons = k
                    break

        if not key_ann or key_cons not in cons.columns:
            raise ValueError("No common non-empty join key found (Gene_symbol/Transcript).")

        # Standardize casing / whitespace
        if key_ann == "Gene_symbol":
            ann[key_ann] = ann[key_ann].astype(str).str.upper().str.strip()
            cons[key_cons] = cons[key_cons].astype(str).str.upper().str.strip()
        else:
            ann[key_ann] = ann[key_ann].astype(str).str.strip()
            cons[key_cons] = cons[key_cons].astype(str).str.strip()

        merged = ann.merge(cons, how=how, left_on=key_ann, right_on=key_cons, suffixes=("", "_constraint"))
        if constraint_version:
            merged["constraint_version"] = constraint_version

        with open_write(out_tsv) as g:
            merged.to_csv(g, sep="\t", index=False)

        matches = merged[key_ann].isin(cons[key_cons].unique()).sum()
        console.log(f"[green]Merged ({how}) on {key_ann} → {out_tsv}  (rows: {len(merged)})")
        if matches == 0:
            console.log("[yellow][merge] WARNING: 0 matching keys; constraint columns likely empty.")

    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
