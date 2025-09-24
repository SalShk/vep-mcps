from __future__ import annotations

from pathlib import Path
from typing import Annotated, List
import sys
import gzip

import pandas as pd
import typer
from rich import print
from rich.table import Table
from rich.console import Console

app = typer.Typer(add_completion=False)
console = Console()

def _open_any(path: Path | str):
    p = str(path)
    if p == "-" or p == "":
        return sys.stdin
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "r", encoding="utf-8")

@app.command()
def main(
    tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv",
            "-i",
            help="TSV to inspect (use '-' for stdin).",
            exists=False,   # allow '-'
            readable=True,
        ),
    ],
    head: Annotated[int, typer.Option("--head", help="Show first N rows of previews")] = 5,
    columns: Annotated[
        List[str] | None,
        typer.Option("--columns", "-c", help="Additional columns to preview (repeatable)"),
    ] = None,
    unique: Annotated[
        List[str] | None,
        typer.Option("--unique", "-u", help="Columns to show unique counts/samples for (repeatable)"),
    ] = None,
    list_columns: Annotated[
        bool,
        typer.Option("--list-columns", help="Only list all columns and exit", is_flag=True),
    ] = False,
    no_keys: Annotated[
        bool,
        typer.Option("--no-keys", help="Skip the Gene_symbol/Transcript/variant_id key summary", is_flag=True),
    ] = False,
) -> None:
    """Quick shape/column checks & key sanity for a TSV."""
    try:
        with _open_any(tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

        n_rows, n_cols = df.shape
        console.rule(f"[bold]Overview: {tsv}")
        print(f"[green]Rows:[/green] {n_rows:,}  [green]Cols:[/green] {n_cols:,}")

        # Column listing mode
        if list_columns:
            tbl = Table(title="All columns", show_header=True, header_style="bold cyan")
            tbl.add_column("#", style="dim", justify="right")
            tbl.add_column("Name")
            for i, col in enumerate(df.columns, 1):
                tbl.add_row(str(i), col)
            console.print(tbl)
            raise typer.Exit(0)

        # Preview first columns (unchanged behavior)
        cols_preview = list(df.columns[: min(12, n_cols)])
        print(f"[cyan]First columns ({len(cols_preview)} of {n_cols}):[/cyan] {cols_preview}")

        # Key columns summary
        if not no_keys:
            keys = [c for c in ("Gene_symbol", "Transcript", "variant_id") if c in df.columns]
            if keys:
                tbl = Table(title="Key columns", show_header=True, header_style="bold magenta")
                tbl.add_column("Column")
                tbl.add_column("Non-empty", justify="right")
                tbl.add_column("Distinct", justify="right")
                tbl.add_column(f"Sample (head {head})")
                for k in keys:
                    col = df[k].astype(str)
                    nonempty = int(col.str.strip().ne("").sum())
                    distinct = col.str.strip().replace({"": None}).nunique(dropna=True)
                    sample = ", ".join(col.head(min(head, len(df))).tolist())
                    tbl.add_row(k, str(nonempty), str(distinct), sample)
                console.print(tbl)

        # Warn on UNKNOWN gene symbols if present
        if "Gene_symbol" in df.columns:
            n_unknown = int((df["Gene_symbol"].astype(str).str.upper().str.strip() == "UNKNOWN").sum())
            if n_unknown:
                print(f"[yellow]WARNING:[/yellow] {n_unknown} rows have Gene_symbol=UNKNOWN.")

        # Compact head of important columns
        base_cols = [c for c in ["variant_id", "Gene_symbol", "Transcript"] if c in df.columns]
        extra_cols = []
        if columns:
            extra_cols = [c for c in columns if c in df.columns and c not in base_cols]
        show_cols = base_cols + extra_cols
        if show_cols:
            print(f"[blue]Head {head} of {show_cols}[/blue]")
            try:
                print(df[show_cols].head(head).to_string(index=False))
            except Exception:
                # fallback if any dtype/mixed issue
                print(df[show_cols].astype(str).head(head).to_string(index=False))

        # Unique summaries for arbitrary columns
        if unique:
            uq_tbl = Table(title=f"Unique summaries (head {head})", show_header=True, header_style="bold green")
            uq_tbl.add_column("Column")
            uq_tbl.add_column("Distinct", justify="right")
            uq_tbl.add_column(f"Values (head {head})")
            for ucol in unique:
                if ucol not in df.columns:
                    uq_tbl.add_row(ucol, "—", "[red]MISSING[/red]")
                    continue
                vals = df[ucol].astype(str).str.strip()
                nunq = vals.replace({"": None}).nunique(dropna=True)
                sample_vals = ", ".join(sorted(set(vals.head(head)))[:head])
                uq_tbl.add_row(ucol, str(nunq), sample_vals)
            console.print(uq_tbl)

    except typer.Exit:
        raise
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()