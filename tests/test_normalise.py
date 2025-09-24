import subprocess
from pathlib import Path
import pandas as pd


def test_normalise_basic(tmp_path: Path):
    # craft minimal filtered TSV (plain .tsv)
    fin = tmp_path / "filtered.tsv"
    fin.write_text(
        "variant_id\tConsequence\tSYMBOL\tFeature\n"
        "chr1:1000:A>G\tmissense_variant\tGeneX\tENST000001\n"
    )

    out = tmp_path / "normalised.tsv"

    cmd = [
        "vep-normalise-columns",
        "--in-tsv", str(fin),
        "--out-tsv", str(out),
        "--vep-cache-version", "109",
        "--plugins-version", "v1.0",
    ]
    assert subprocess.call(cmd) == 0

    df = pd.read_csv(out, sep="\t", dtype=str)
    # columns normalized
    assert "Gene_symbol" in df.columns
    assert "Transcript" in df.columns
    # values normalized
    assert df.loc[0, "Gene_symbol"] == "GENEX"
    assert df.loc[0, "Transcript"] == "ENST000001"
    # metadata present
    assert df.loc[0, "vep_cache_version"] == "109"
    assert df.loc[0, "plugins_version"] == "v1.0"
