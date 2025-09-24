from __future__ import annotations

from pathlib import Path
from typing import Annotated
import gzip
import re

import pandas as pd
import typer
from rich import print

app = typer.Typer(add_completion=False)

# e.g. "NM_000001.1:c.100A>G" → "NM_000001.1"
NM_RE = re.compile(r"\b(NM_\d+(?:\.\d+)?)")

def _open_read(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return open(path, "r", encoding="utf-8")

def _open_write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if str(path).endswith(".gz"):
        return gzip.open(path, "wt", encoding="utf-8")
    return open(path, "w", encoding="utf-8")

def infer_transcript_from_hgvs(hgvs: str | None) -> str | None:
    if hgvs is None or str(hgvs).strip() == "":
        return None
    m = NM_RE.search(str(hgvs))
    return m.group(1) if m else None

def load_tx2gene_map(path: str | None) -> dict[str, str]:
    """Load a simple TSV with columns: Transcript, Gene_symbol"""
    if not path:
        return {}
    df = pd.read_table(path, dtype=str).fillna("")
    for c in ("Transcript", "Gene_symbol"):
        if c not in df.columns:
            raise ValueError("tx2gene file must have columns: Transcript, Gene_symbol")
    df["Transcript"] = df["Transcript"].str.strip()
    df["Gene_symbol"] = df["Gene_symbol"].str.upper().str.strip()
    return dict(zip(df["Transcript"], df["Gene_symbol"]))

@app.command()
def main(
    in_tsv: Annotated[
        Path,
        typer.Option(
            "--in-tsv",
            "-i",
            help="Input TSV file from VEP (post-filter).",
            exists=True,
            readable=True,
        ),
    ],
    out_tsv: Annotated[
        Path,
        typer.Option(
            "--out-tsv",
            "-o",
            help="Output TSV with normalised columns.",
            writable=True,
        ),
    ],
    vep_cache_version: Annotated[str | None, typer.Option("--vep-cache-version")] = None,
    plugins_version: Annotated[str | None, typer.Option("--plugins-version")] = None,
    gene_column: Annotated[
        str | None,
        typer.Option(
            "--gene-column",
            help="Use this source column as Gene_symbol (e.g., SYMBOL).",
        ),
    ] = None,
    tx2gene: Annotated[
        str | None,
        typer.Option(
            "--tx2gene",
            help="Optional transcript→gene map TSV with columns: Transcript, Gene_symbol.",
        ),
    ] = None,
) -> None:
    """Normalise VEP TSV columns and populate Gene_symbol/Transcript when possible."""
    try:
        print(f"[debug] Reading input: {in_tsv}")
        with _open_read(in_tsv) as fin:
            df = pd.read_csv(fin, sep="\t", dtype=str, low_memory=False).fillna("")

        print(f"[debug] Original columns: {list(df.columns)}")

        # Canonical renames (apply only if present)
        column_mapping = {
            # Gene symbol synonyms → Gene_symbol
            "SYMBOL": "Gene_symbol",
            "Gene": "Gene_symbol",
            "Gene_name": "Gene_symbol",
            "symbol": "Gene_symbol",
            "GENE_PHENO": "Gene_pheno",  # keep for reference

            # Transcript synonyms → Transcript
            "Feature": "Transcript",
            "feature": "Transcript",
            "Feature_type": "Transcript",
            "Transcript_ID": "Transcript",
            "transcript_id": "Transcript",

            # dbSNP synonyms → dbSNP
            "Existing_variation": "dbSNP",
            "RSID": "dbSNP",
            "dbsnp": "dbSNP",
            "rs_dbSNP": "dbSNP",
        }
        mapping_to_apply = {k: v for k, v in column_mapping.items() if k in df.columns}
        if mapping_to_apply:
            df = df.rename(columns=mapping_to_apply)
            print(f"[debug] Applied column mappings: {mapping_to_apply}")
        else:
            print("[debug] No column mappings applied.")

        # Ensure canonical columns exist
        if "Gene_symbol" not in df.columns:
            df["Gene_symbol"] = ""
        if "Transcript" not in df.columns:
            df["Transcript"] = ""

        # If user provided a specific gene column, use it
        if gene_column and gene_column in df.columns:
            df["Gene_symbol"] = df[gene_column].astype(str)

        # Infer Transcript from clinvar_hgvs if we still don't have any
        if (df["Transcript"] == "").all() and "clinvar_hgvs" in df.columns:
            df["Transcript"] = df["clinvar_hgvs"].apply(infer_transcript_from_hgvs).fillna("")

        # If Gene_symbol still empty, try transcript→gene map
        tx2gene_map = load_tx2gene_map(tx2gene)
        if tx2gene_map and (df["Gene_symbol"] == "").any():
            df.loc[df["Gene_symbol"] == "", "Gene_symbol"] = (
                df.loc[df["Gene_symbol"] == "", "Transcript"].map(tx2gene_map).fillna("")
            )

        # Final standardisation
        df["Gene_symbol"] = df["Gene_symbol"].astype(str).str.upper().str.strip().replace({"": "UNKNOWN"})
        df["Transcript"] = df["Transcript"].astype(str).str.strip()

        # Add metadata if provided
        if vep_cache_version:
            df["vep_cache_version"] = vep_cache_version
        if plugins_version:
            df["plugins_version"] = plugins_version

        # Write out
        with _open_write(out_tsv) as fout:
            df.to_csv(fout, sep="\t", index=False)

        print(f"[green]Normalized columns and wrote {out_tsv} (rows: {len(df)})")
        unk = (df["Gene_symbol"] == "UNKNOWN").sum()
        if unk:
            print("[yellow][normalise] WARNING: "
                  f"{unk} rows have Gene_symbol=UNKNOWN. "
                  "Provide --gene-column SYMBOL or a --tx2gene map for gene-level merge.")

    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
