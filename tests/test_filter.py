import os, subprocess, gzip, pandas as pd

def test_filter_runs(tmp_path):
    # create tiny input
    p = tmp_path/"in.tsv.gz"
    with gzip.open(p, "wt") as f:
        f.write("Consequence\tCANONICAL\tMANE\nmissense_variant\tYES\tENST\nsynonymous_variant\tNO\t\n")
    out = tmp_path/"out.tsv.gz"
    cmd = [
        "python","-m","vep_parser_mcp.cli.filter_consequence_and_mane",
        "--in-tsv", str(p),
        "--out-tsv", str(out),
        "--keep-consequence","missense_variant",
        "--require-canonical"
    ]
    assert subprocess.call(cmd) == 0
    with gzip.open(out, "rt") as g:
        df = pd.read_csv(g, sep="\t")
    assert len(df) == 1
