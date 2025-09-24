from __future__ import annotations

from pathlib import Path
from typing import Annotated
import pandas as pd
import typer
from rich import print
import gzip
import re

app = typer.Typer()

def extract_gene_symbol(gene_pheno: str) -> str:
    """Extract gene symbol from GENE_PHENO column."""
    if not gene_pheno or pd.isna(gene_pheno) or gene_pheno.lower() in ['nan', 'none', '']:
        return ''
    
    # Try to extract gene symbol - common patterns:
    # "Gene associated with disease" -> try to find actual gene symbol elsewhere or return empty
    # For now, return the original value, but we need a better approach
    return str(gene_pheno).strip()

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
            help="Output TSV file with normalized columns",
            show_default=False,
            writable=True,
        ),
    ],
    vep_cache_version: Annotated[
        str,
        typer.Option(
            "--vep-cache-version",
            help="VEP cache version for metadata",
        ),
    ] = None,
    plugins_version: Annotated[
        str,
        typer.Option(
            "--plugins-version", 
            help="VEP plugins version for metadata",
        ),
    ] = None,
) -> None:
    """Normalize VEP TSV columns to standard format."""
    try:
        print(f"[debug] Reading input: {in_tsv}")
        
        if str(in_tsv).endswith('.gz'):
            with gzip.open(in_tsv, 'rt') as f:
                df = pd.read_csv(f, sep="\t", dtype=str, low_memory=False)
        else:
            df = pd.read_csv(in_tsv, sep="\t", dtype=str, low_memory=False)

        print(f"[debug] Original columns: {list(df.columns)}")
        
        # More comprehensive column name normalization
        column_mapping = {
            # Gene symbol mappings
            'SYMBOL': 'Gene_symbol',
            'Gene': 'Gene_symbol',
            'Gene_name': 'Gene_symbol',
            'symbol': 'Gene_symbol',
            'GENE_PHENO': 'Gene_pheno',  # Keep original for reference
            
            # Transcript mappings
            'Feature': 'Transcript',
            'Feature_type': 'Transcript',
            'Transcript_ID': 'Transcript',
            'transcript_id': 'Transcript',
            
            # dbSNP mappings
            'Existing_variation': 'dbSNP',
            'RSID': 'dbSNP',
            'dbsnp': 'dbSNP',
            'rs_dbSNP': 'dbSNP',
        }
        
        # Only rename columns that actually exist
        existing_columns = set(df.columns)
        mapping_to_apply = {old: new for old, new in column_mapping.items() if old in existing_columns}
        
        if mapping_to_apply:
            df = df.rename(columns=mapping_to_apply)
            print(f"[debug] Applied column mappings: {mapping_to_apply}")
        else:
            print("[debug] No column mappings applied - using original column names")
        
        # Create Gene_symbol column if it doesn't exist
        if 'Gene_symbol' not in df.columns:
            # Try to extract from variant_id or other columns
            if 'variant_id' in df.columns:
                # Extract gene from variant_id pattern like "chr1:1000:A>G"
                # For real data, you might need a different approach
                df['Gene_symbol'] = 'UNKNOWN'  # Placeholder
                print("[debug] Created placeholder Gene_symbol column")
            else:
                df['Gene_symbol'] = 'UNKNOWN'
                print("[debug] Created placeholder Gene_symbol column")
        
        print(f"[debug] Final columns: {list(df.columns)}")
        
        # Add metadata if provided
        if vep_cache_version:
            df['vep_cache_version'] = vep_cache_version
        if plugins_version:
            df['plugins_version'] = plugins_version

        out_tsv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_tsv, sep="\t", index=False)
        print(f"[green]Normalized columns and wrote {out_tsv} (rows: {len(df)})")
        
        # Show sample of Gene_symbol values for debugging
        if 'Gene_symbol' in df.columns:
            print(f"[debug] Sample Gene_symbol values: {df['Gene_symbol'].head(2).tolist()}")
        
    except Exception as e:
        print(f"[red]Error: {e}")
        raise typer.Exit(code=1) from None

if __name__ == "__main__":
    app()