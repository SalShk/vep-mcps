from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer
from rich import print

def main(
    in_tsv: Annotated[
        Path, typer.Option("--in-tsv", "-i", help="Input TSV file from VEP")
    ],
    out_tsv: Annotated[
        Path, typer.Option("--out-tsv", "-o", help="Output TSV file")
    ],
    vep_cache_version: Annotated[
        str, typer.Option("--vep-cache-version", "-v", help="VEP cache version")
    ],
    plugins_version: Annotated[
        str, typer.Option("--plugins-version", "-p", help="VEP plugins version")
    ],
) -> None:
    """Normalise VEP TSV columns and add version metadata."""
    try:
        print(f"[debug] Reading input: {in_tsv}")
        df = pd.read_csv(in_tsv, sep="\t", dtype=str, low_memory=False)

        df.columns = [c.strip() for c in df.columns]

        if "SYMBOL" in df.columns and "Gene_symbol" not in df.columns:
            df["Gene_symbol"] = df["SYMBOL"]
        elif "Gene_symbol" not in df.columns:
            df["Gene_symbol"] = ""
        if "Feature" in df.columns and "Transcript" not in df.columns:
            df["Transcript"] = df["Feature"]

        df["vep_cache_version"] = vep_cache_version
        df["plugins_version"] = plugins_version

        out_tsv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_tsv, sep="\t", index=False)
        print(f"[green]Wrote {out_tsv}")
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1) from None

if __name__ == "__main__":
    typer.run(main)