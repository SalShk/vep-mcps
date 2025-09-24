from __future__ import annotations

from pathlib import Path
from typing import Annotated
import gzip

import pandas as pd
import typer
from rich import print
from rich.table import Table
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

def _open(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")

@app.command()
def main(
    tsv: Annotated[Path, typer.Option("--in-tsv", "-i", help="TSV to inspect", exists=True, readable=True)],
    head: int = typer.Option(5, "--head", help="Show first N rows of selected columns"),
) -> None:
    """Quick shape/column checks & key sanity for a TSV."""
    try:
        with _open(tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

        n_rows, n_cols = df.shape
        console.rule(f"[bold]Overview: {tsv}")
        print(f"[green]Rows:[/green] {n_rows:,}  [green]Cols:[/green] {n_cols:,}")

        cols_preview = list(df.columns[:12])
        print(f"[cyan]First columns ({len(cols_preview)} of {n_cols}):[/cyan] {cols_preview}")

        keys = [c for c in ("Gene_symbol", "Transcript", "variant_id") if c in df.columns]
        if keys:
            tbl = Table(title="Key columns", show_header=True, header_style="bold magenta")
            tbl.add_column("Column"); tbl.add_column("Non-empty"); tbl.add_column("Distinct"); tbl.add_column("Sample (head)")
            for k in keys:
                nonempty = int(df[k].astype(str).str.strip().ne("").sum())
                distinct = df[k].astype(str).str.strip().replace({"": None}).nunique(dropna=True)
                sample = ", ".join(df[k].astype(str).head(min(head, len(df))).tolist())
                tbl.add_row(k, str(nonempty), str(distinct), sample)
            console.print(tbl)

        if "Gene_symbol" in df.columns:
            n_unknown = int((df["Gene_symbol"].astype(str).str.upper().str.strip() == "UNKNOWN").sum())
            if n_unknown:
                print(f"[yellow]WARNING:[/yellow] {n_unknown} rows have Gene_symbol=UNKNOWN.")

        show_cols = [c for c in ["variant_id", "Gene_symbol", "Transcript"] if c in df.columns]
        if show_cols:
            print(f"[blue]Head {head} of {show_cols}[/blue]")
            print(df[show_cols].head(head).to_string(index=False))

    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
