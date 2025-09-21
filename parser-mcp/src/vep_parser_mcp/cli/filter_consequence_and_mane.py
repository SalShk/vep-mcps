from __future__ import annotations

import pandas as pd
import typer
from rich.console import Console

from ..io.gz import open_read, open_write

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def main(
    in_tsv: str = typer.Option(
        ..., "--in-tsv", help="Input VEP tabular file (.tsv or .tsv.gz)"
    ),
    out_tsv: str = typer.Option(
        ..., "--out-tsv", help="Output filtered VEP tabular file"
    ),
    keep_consequence: list[str] = typer.Option(
        ...,
        "--keep-consequence",
        help="Comma-separated consequences to keep (e.g. missense_variant,stop_gained)",
    ),
    require_canonical: bool = typer.Option(
        False, "--require-canonical", help="Keep only rows with CANONICAL=YES"
    ),
    require_mane: bool = typer.Option(
        False, "--require-mane", help="Require MANE/MANE_SELECT to be present"
    ),
) -> None:
    """
    Filter VEP tabular output by consequence and optionally CANONICAL/MANE.
    Preserves the same column layout for downstream tools.
    """
    try:
        # Split comma-separated keep_consequence values if passed as a single string.
        if (
            len(keep_consequence) == 1
            and isinstance(keep_consequence[0], str)
            and "," in keep_consequence[0]
        ):
            keep_consequence = [
                c.strip() for c in keep_consequence[0].split(",") if c.strip()
            ]

        with open_read(in_tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

        if "Consequence" not in df.columns:
            raise ValueError("Missing 'Consequence' column in input.")

        mask = df["Consequence"].isin(keep_consequence)

        if require_canonical:
            if "CANONICAL" in df.columns:
                mask &= df["CANONICAL"].fillna("") == "YES"
            else:
                console.log(
                    "[yellow]Column 'CANONICAL' not found; '--require-canonical' ignored."
                )

        if require_mane:
            mane_col = (
                "MANE_SELECT"
                if "MANE_SELECT" in df.columns
                else ("MANE" if "MANE" in df.columns else None)
            )
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
        raise typer.Exit(code=1) from e
