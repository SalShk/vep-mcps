from __future__ import annotations

from pathlib import Path
from typing import Annotated
import gzip

import pandas as pd
import typer
from rich import print

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _open_read(path: Path):
    """Open TSV (optionally .gz) for reading."""
    p = str(path)
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "r", encoding="utf-8")


def _open_write(path: Path):
    """Open TSV (optionally .gz) for writing. Creates parent dir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    p = str(path)
    if p.endswith(".gz"):
        return gzip.open(p, "wt", encoding="utf-8")
    return open(p, "w", encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# Command
# ──────────────────────────────────────────────────────────────────────────────

def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv", "-i",
            help="Input TSV file from VEP (.tsv or .tsv.gz).",
            exists=True, readable=True,
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv", "-o",
            help="Output TSV file (.tsv or .tsv.gz).",
            writable=True,
        ),
    ],
    keep_consequence: Annotated[
        str,
        typer.Option(
            "--keep-consequence", "-c",
            help="Comma-separated consequences to keep (case-sensitive; "
                 "matches any term within '&' lists).",
            show_default=True,
        ),
    ] = "missense_variant,stop_gained",
    mane_only: Annotated[
        bool,
        typer.Option(
            "--mane-only",
            help="Keep only MANE select transcripts (detects one of: MANE, MANE_select, MANE_SELECT).",
            is_flag=True,
        ),
    ] = False,
    require_canonical: Annotated[
        bool,
        typer.Option(
            "--require-canonical",
            help="Keep only canonical transcripts (requires CANONICAL == 'YES').",
            is_flag=True,
        ),
    ] = False,
) -> None:
    """
    Filter VEP TSV by consequence and optionally by MANE and/or CANONICAL.
    Supports gzipped input/output.
    """
    try:
        print(f"[debug] Reading input: {in_tsv}")
        with _open_read(in_tsv) as f:
            df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)

        # Required column
        cons_col = "Consequence"
        if cons_col not in df.columns:
            raise ValueError(f"Missing column '{cons_col}' in {in_tsv}")

        # Optional columns
        mane_candidates = ["MANE", "MANE_select", "MANE_SELECT"]
        mane_col = next((c for c in mane_candidates if c in df.columns), None)
        if mane_only and mane_col is None:
            raise ValueError(
                f"--mane-only requested but none of MANE columns present: {mane_candidates}"
            )

        canon_col = "CANONICAL"
        if require_canonical and canon_col not in df.columns:
            raise ValueError(f"--require-canonical requested but column '{canon_col}' not present")

        # Consequence filter
        keep = {c.strip() for c in keep_consequence.split(",") if c.strip()}
        print(f"[debug] Filtering for consequences: {keep}")

        def _has_kept_consequence(s: str) -> bool:
            if not isinstance(s, str) or not s or s.lower() == "nan":
                return False
            # Split on commas *then* split on '&' to support both separators safely
            parts: list[str] = []
            for chunk in s.split(","):
                parts.extend(p.strip() for p in chunk.split("&"))
            return any(p in keep for p in parts if p)

        before_n = len(df)
        df = df[df[cons_col].map(_has_kept_consequence)]
        print(f"[debug] Consequence filter: {before_n} → {len(df)} rows")

        # Canonical filter
        if require_canonical:
            truth = df[canon_col].astype(str).str.strip().str.upper().eq("YES")
            df = df[truth]
            print(f"[debug] After CANONICAL filter: {len(df)} rows")

        # MANE filter
        if mane_only:
            # Treat any non-empty as truthy (many VEP runs store the MANE transcript string here)
            truthy = df[mane_col].astype(str).str.strip().ne("")
            df = df[truthy]
            print(f"[debug] After MANE filter ({mane_col} non-empty): {len(df)} rows")

        with _open_write(out_tsv) as g:
            df.to_csv(g, sep="\t", index=False)
        print(f"[green]Wrote {out_tsv}")

    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1) from None


# ──────────────────────────────────────────────────────────────────────────────
# Entry point for both console-script and `python -m ...`
# ──────────────────────────────────────────────────────────────────────────────

def cli() -> None:
    """Entry point wrapper (console scripts & `python -m ...`)."""
    typer.run(main)


if __name__ == "__main__":
    cli()
