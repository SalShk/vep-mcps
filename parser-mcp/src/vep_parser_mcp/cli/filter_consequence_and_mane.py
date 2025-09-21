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
        str, typer.Option(..., "--in-tsv", help="Input VEP TSV (.tsv or .tsv.gz)")
    ],
    out_tsv: Annotated[str, typer.Option(..., "--out-tsv", help="Output filtered TSV")],
    keep_consequence: Annotated[
        list[str],
        typer.Option(..., "--keep-consequence", help="Comma-separated list allowed"),
    ],
    require_canonical: Annotated[
        bool, typer.Option(False, "--require-canonical", help="Keep only CANONICAL=YES")
    ] = False,
    require_mane: Annotated[
        bool,
        typer.Option(False, "--require-mane", help="Require MANE/MANE_SELECT present"),
    ] = False,
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

        # Typer parses comma-separated strings into list; split again defensively
        keep: set[str] = set()
        for item in keep_consequence:
            keep.update({c.strip() for c in str(item).split(",") if c.strip()})

        mask = df["Consequence"].isin(keep)

        if require_canonical and "CANONICAL" in df.columns:
            mask &= df["CANONICAL"].fillna("").eq("YES")

        if require_mane:
            mane_col = (
                "MANE_SELECT"
                if "MANE_SELECT" in df.columns
                else ("MANE" if "MANE" in df.columns else None)
            )
            if mane_col:
                mask &= df[mane_col].notna() & df[mane_col].astype(str).ne("")
            else:
                console.log("[yellow]MANE column not found; '--require-mane' ignored.")

        out = df.loc[mask].copy()

        with open_write(out_tsv) as g:
            out.to_csv(g, sep="\t", index=False)

        console.log(f"[green]Filtered rows: {len(out)} (from {len(df)}) → {out_tsv}")
    except Exception as e:
        console.log(f"[red]Error: {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
