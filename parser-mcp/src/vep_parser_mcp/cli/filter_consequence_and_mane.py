from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer
from rich import print

app = typer.Typer(help="Filter VEP TSV by consequence and optionally MANE select transcripts.")

@app.command()
def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv",
            "-i",
            help="Input TSV file from VEP",
            show_default=False,
            exists=True,
            readable=True,
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv",
            "-o",
            help="Output TSV file",
            show_default=False,
            writable=True,
        ),
    ],
    keep_consequence: Annotated[
        str,
        typer.Option(
            "--keep-consequence",
            "-c",
            help="Comma-separated consequences to keep",
            show_default=True,
        ),
    ] = "missense_variant,stop_gained",
    mane_only: Annotated[
        bool,
        typer.Option(
            "--mane-only",
            help="Keep only MANE select transcripts",
            is_flag=True,
        ),
    ] = False,
) -> None:
    """Filter VEP TSV by consequence and optionally MANE select transcripts."""
    try:
        print(f"[debug] Reading input: {in_tsv}")
        df = pd.read_csv(in_tsv, sep="\t", dtype=str, low_memory=False)

        cons_col = "Consequence"
        mane_col = "MANE_select"
        if cons_col not in df.columns:
            raise ValueError(f"Missing column '{cons_col}' in {in_tsv}")

        keep = {c.strip() for c in keep_consequence.split(",") if c.strip()}
        print(f"[debug] Filtering for consequences: {keep}")

        def _has_kept_consequence(s: str) -> bool:
            if not s or s.lower() == "nan":
                return False
            parts = [p.strip() for p in s.split("&")]
            return any(p in keep for p in parts)

        df = df[df[cons_col].astype(str).map(_has_kept_consequence)]
        print(f"[debug] Filtered to {len(df)} rows")

        if mane_only:
            if mane_col not in df.columns:
                raise ValueError(f"Missing column '{mane_col}' needed for --mane-only")
            truthy = {"yes", "true", "1", "y", "t"}
            df = df[df[mane_col].astype(str).str.strip().str.lower().isin(truthy)]
            print(f"[debug] After MANE filter: {len(df)} rows")

        out_tsv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_tsv, sep="\t", index=False)
        print(f"[green]Wrote {out_tsv}")
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1) from None

if __name__ == "__main__":
    app()