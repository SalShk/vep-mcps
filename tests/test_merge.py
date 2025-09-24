import subprocess
from pathlib import Path
import pandas as pd


def test_merge_transcript_left_join(tmp_path: Path):
    # normalised annotation (what the previous step produces)
    ann = tmp_path / "normalised.tsv"
    ann.write_text(
        "variant_id\tGene_symbol\tTranscript\tConsequence\n"
        "chr1:1000:A>G\tGENE1\tENST000001\tmissense_variant\n"
        "chr2:2000:T>A\tGENE2\tENST000002\tstop_gained\n"
    )

    # constraint table keyed by 'transcript'
    cons = tmp_path / "constraint.tsv"
    cons.write_text(
        "transcript\tOE_LOF_UPPER\tpLI\n"
        "ENST000001\t0.45\t0.98\n"
        "ENST000002\t0.85\t0.10\n"
    )

    out = tmp_path / "merged.tsv"

    cmd = [
        "vep-merge-gnomad-constraint",
        "--in-tsv", str(ann),
        "--constraint-tsv", str(cons),
        "--out-tsv", str(out),
        "--on", "transcript",
        "--how", "left",
        "--constraint-version", "gnomad3.1",
    ]
    assert subprocess.call(cmd) == 0

    df = pd.read_csv(out, sep="\t", dtype=str)
    # joined columns present
    assert "OE_LOF_UPPER" in df.columns and "pLI" in df.columns
    # both rows retained (left join)
    assert len(df) == 2
    # values merged correctly
    row1 = df[df["Transcript"] == "ENST000001"].iloc[0]
    assert row1["OE_LOF_UPPER"] == "0.45" and row1["pLI"] == "0.98"
    # version annotation propagated
    assert (df["constraint_version"] == "gnomad3.1").all()
