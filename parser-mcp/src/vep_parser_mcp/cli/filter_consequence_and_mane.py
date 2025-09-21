from __future__ import annotations
import sys
from typing import List
import typer
import pandas as pd
from rich.console import Console
from ..io.gz import open_read, open_write

app = typer.Typer(add_completion=False)
console = Console()

@app.command()
def app(
    in_tsv: str = typer.Option(..., "--in-tsv", help="Input VEP tabular file (.tsv or .tsv.gz)"),
    out_tsv: str = typer.Option(..., "--out-tsv", help="Output filtered VEP tabular file"),
    keep_consequence: List[str] = typer.Option(..., "--keep-consequence", help="Consequences to keep"),
    require_canonical: bool = typer.Option(False, "--require-canonical", help="Keep only CANONICAL=YES"),
    require_mane: bool = typer.Option(False, "--require-mane", help="Require MANE/MANE_SELECT present"),
) -> None:
    """
    Filter VEP tabular output by consequence and optionally CANONICAL/MANE.
    Preserves the same column layout for downstream tools.
    """
    try:
        with open_read(in_tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)
        if "Consequence" not in df.columns:
            raise ValueError("Missing 'Consequence' column in input.")

        mask = df["Consequence"].isin(keep_consequence)
        if require_canonical and "CANONICAL" in df.columns:
            mask &= (df["CANONICAL"].fillna("") == "YES")
        if require_mane:
            mane_col = "MANE_SELECT" if "MANE_SELECT" in df.columns else ("MANE" if "MANE" in df.columns else None)
            if mane_col:
                mask &= df[mane_col].notna() & (df[mane_col].astype(str) != "")
            else:
                console.log("[yellow]MANE column not found; '--require-mane' ignored.")
        out = df.loc[mask].copy()

        with open_write(out_tsv) as g:
            out.to_csv(g, sep="\t", index=False)

        console.log(f"[green]Filtered rows: {len(out)} (from {len(df)}) → {out_tsv}")
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1)
