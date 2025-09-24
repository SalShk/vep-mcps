import gzip
import subprocess
from pathlib import Path
import pandas as pd


def test_filter_runs(tmp_path: Path):
    # input
    p = tmp_path / "in.tsv.gz"
    with gzip.open(p, "wt") as f:
        f.write(
            "Consequence\tCANONICAL\tMANE\n"
            "missense_variant\tYES\tENST\n"
            "synonymous_variant\tNO\t\n"
        )

    out = tmp_path / "out.tsv.gz"

    # ✅ test the console script
    cmd = [
        "vep-filter-consequence-mane",
        "--in-tsv", str(p),
        "--out-tsv", str(out),
        "--keep-consequence", "missense_variant",
        "--require-canonical",
    ]
    assert subprocess.call(cmd) == 0

    # verify
    with gzip.open(out, "rt") as g:
        df = pd.read_csv(g, sep="\t")
    assert len(df) == 1
    assert df["Consequence"].iloc[0] == "missense_variant"
    assert df["MANE"].iloc[0] != "" or "MANE_SELECT" in df.columns  # tolerate column name variants
