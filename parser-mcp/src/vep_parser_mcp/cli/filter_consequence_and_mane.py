from __future__ import annotations

from pathlib import Path
from typing import Annotated
import gzip

import pandas as pd
import typer
from rich import print

app = typer.Typer(
    add_completion=False,
    help="Filter VEP TSV by consequence and optionally MANE / CANONICAL.",
)

def _open(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")

@app.command()
def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv", "-i",
            help="Input TSV file from VEP",
            exists=True, readable=True,
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv", "-o",
            help="Output TSV file",
            writable=True,
        ),
    ],
    keep_consequence: Annotated[
        str,
        typer.Option(
            "--keep-consequence", "-c",
            help="Comma-separated consequences to keep (case-sensitive, matches any in '&' lists).",
            show_default=True,
        ),
    ] = "missense_variant,stop_gained",
    mane_only: Annotated[
        bool,
        typer.Option(
            "--mane-only",
            help="Keep only MANE select transcripts (detects columns: MANE, MANE_select, MANE_SELECT).",
            is_flag=True,
        ),
    ] = False,
    require_canonical: Annotated[
        bool,
        typer.Option(
            "--require-canonical",
            help="Keep only canonical transcripts (requires CANONICAL=='YES').",
            is_flag=True,
        ),
    ] = False,
) -> None:
    """
    Filter VEP TSV by consequence, and optionally by MANE and/or CANONICAL.
    """
    try:
        print(f"[debug] Reading input: {in_tsv}")
        with _open(in_tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

        # --- columns presence / detection
        cons_col = "Consequence"
        if cons_col not in df.columns:
            raise ValueError(f"Missing column '{cons_col}' in {in_tsv}")

        # Flexible MANE column names
        mane_candidates = ["MANE", "MANE_select", "MANE_SELECT"]
        mane_col = next((c for c in mane_candidates if c in df.columns), None)
        if mane_only and mane_col is None:
            raise ValueError(f"--mane-only requested but none of MANE columns present: {mane_candidates}")

        # Canonical column (strict name used by many VEP runs)
        canon_col = "CANONICAL"
        if require_canonical and canon_col not in df.columns:
            raise ValueError(f"--require-canonical requested but column '{canon_col}' not present")

        # --- consequence filter
        keep = {c.strip() for c in keep_consequence.split(",") if c.strip()}
        print(f"[debug] Filtering for consequences: {keep}")

        def has_kept_consequence(s: str) -> bool:
            if not isinstance(s, str) or not s or s.lower() == "nan":
                return False
            # support either "a&b&c" or accidental commas
            parts = []
            for chunk in s.split(","):
                parts.extend(p.strip() for p in chunk.split("&"))
            return any(p in keep for p in parts)

        before = len(df)
        df = df[df[cons_col].map(has_kept_consequence)]
        print(f"[debug] Consequence filter: {before} → {len(df)} rows")

        # --- canonical (if requested)
        if require_canonical:
            truth = df[canon_col].astype(str).str.strip().str.upper().eq("YES")
            df = df[truth]
            print(f"[debug] After CANONICAL filter: {len(df)} rows")

        # --- MANE (if requested)
        if mane_only:
            # treat any non-empty as truthy for MANE presence; many VEP runs store MANE transcript id here
            truthy = df[mane_col].astype(str).str.strip().ne("")
            df = df[truthy]
            print(f"[debug] After MANE filter ({mane_col} non-empty): {len(df)} rows")

        out_tsv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_tsv, sep="\t", index=False)
        print(f"[green]Wrote {out_tsv}")
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    # Makes `python -m vep_parser_mcp.cli.filter_consequence_and_mane ...`
    # work without needing a subcommand.
    import typer
    typer.run(main)