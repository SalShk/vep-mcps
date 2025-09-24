from __future__ import annotations

from pathlib import Path
from typing import Annotated, Iterable
import os
import sys
import gzip

import pandas as pd
import typer
from rich import print

app = typer.Typer(
    add_completion=False,
    help="Filter VEP TSV by consequence and optionally MANE select transcripts."
)

# -------- I/O helpers: stdin/stdout + .gz --------
def open_read_any(path: Path | str):
    p = str(path)
    if p == "-" or p == "":
        return sys.stdin
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "r", encoding="utf-8")

def open_write_any(path: Path | str):
    p = str(path)
    if p == "-" or p == "":
        return sys.stdout
    os.makedirs(str(Path(p).parent), exist_ok=True)
    if p.endswith(".gz"):
        return gzip.open(p, "wt", encoding="utf-8")
    return open(p, "w", encoding="utf-8")

# -------- small utils --------
def _find_first(cols: Iterable[str], candidates: list[str]) -> str | None:
    s = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in s:
            return s[cand.lower()]
    return None

def _split_terms(s: str) -> list[str]:
    # VEP often uses & between consequences, but we also accept comma/semicolon
    for sep in ("&", ",", ";"):
        if sep in s:
            return [p.strip() for p in s.split(sep) if p.strip()]
    return [s.strip()] if s.strip() else []

@app.command()
def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv", "-i",
            help="Input TSV file from VEP (use '-' for stdin)",
            show_default=False,
            exists=False,  # we support stdin, so can't require exists=True
            readable=True,
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv", "-o",
            help="Output TSV file (use '-' for stdout)",
            show_default=False,
            writable=True,
        ),
    ],
    keep_consequence: Annotated[
        str,
        typer.Option(
            "--keep-consequence", "-c",
            help="Comma-separated consequences to keep (case-sensitive VEP terms). "
                 "If empty, no consequence filtering is applied.",
            show_default=True,
        ),
    ] = "missense_variant,stop_gained",
    mane_only: Annotated[
        bool,
        typer.Option(
            "--mane-only",
            help="Keep only MANE select transcripts "
                 "(auto-detects MANE column name: MANE_SELECT / MANE_select / MANE / mane_select).",
            is_flag=True,
        ),
    ] = False,
) -> None:
    """Filter VEP TSV by consequence and optionally MANE select transcripts."""
    try:
        print(f"[debug] Reading input: {in_tsv}")
        with open_read_any(in_tsv) as fin:
            df = pd.read_csv(fin, sep="\t", dtype=str, low_memory=False).fillna("")

        # Column detection
        cons_col = _find_first(df.columns, ["Consequence"])
        if not cons_col:
            raise ValueError("Missing 'Consequence' column in input.")

        mane_col = _find_first(df.columns, ["MANE_SELECT", "MANE_select", "MANE", "mane_select"])

        # Build keep set (allow empty = no filtering)
        keep_set = {c.strip() for c in keep_consequence.split(",") if c.strip()}
        print(f"[debug] Filtering for consequences: {keep_set or '(none — pass-through)'}")

        if keep_set:
            def has_kept(x: str) -> bool:
                return any(term in keep_set for term in _split_terms(str(x)))
            before = len(df)
            df = df[df[cons_col].map(has_kept)]
            print(f"[debug] Consequence filter: {before} → {len(df)} rows")

        if mane_only:
            if not mane_col:
                raise ValueError("Requested --mane-only but no MANE column was found "
                                 "(looked for MANE_SELECT / MANE_select / MANE / mane_select).")
            truthy = {"yes", "true", "1", "y", "t"}
            before = len(df)
            df = df[df[mane_col].astype(str).str.strip().str.lower().isin(truthy)]
            print(f"[debug] MANE filter: {before} → {len(df)} rows (column: {mane_col})")

        with open_write_any(out_tsv) as fout:
            df.to_csv(fout, sep="\t", index=False)
        print(f"[green]Wrote {out_tsv}")
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1) from None

if __name__ == "__main__":
    app()
