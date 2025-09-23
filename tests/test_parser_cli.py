import subprocess
from pathlib import Path
import pytest

IMAGE = "vep-parser-mcp:0.1.0"
TESTS = Path("/workspaces/vep-mcps/tests/data")


def run_docker(args, tmp_path):
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{Path.cwd()}:/wd",
        "-v",
        f"{tmp_path}:/tmp",
        "-w",
        "/wd",
        IMAGE,
    ] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def test_01_filter_runs(tmp_path):
    out_tsv = tmp_path / "filtered.tsv"
    result = run_docker(
        [
            "vep-filter-consequence-mane",
            "--in-tsv",
            str(TESTS / "tiny.vep.tsv"),
            "--out-tsv",
            str(out_tsv),
            "--keep-consequence",
            "missense_variant,stop_gained",
        ],
        tmp_path,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert out_tsv.exists()
    assert out_tsv.stat().st_size > 0


def test_02_normalise_runs(tmp_path):
    in_tsv = tmp_path / "filtered.tsv"
    out_tsv = tmp_path / "normalised.tsv"
    result = run_docker(
        [
            "vep-normalise-columns",
            "--in-tsv",
            str(in_tsv),
            "--out-tsv",
            str(out_tsv),
            "--vep-cache-version",
            "110",
            "--plugins-version",
            "2025-09-01",
        ],
        tmp_path,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert out_tsv.exists()
    txt = out_tsv.read_text().splitlines()[0]
    assert "vep_cache_version" in txt and "plugins_version" in txt


def test_03_merge_runs(tmp_path):
    in_tsv = tmp_path / "normalised.tsv"
    out_tsv = tmp_path / "merged.tsv"
    result = run_docker(
        [
            "vep-merge-gnomad-constraint",
            "--in-tsv",
            str(in_tsv),
            "--constraint-tsv",
            str(TESTS / "tiny.constraint.tsv"),
            "--on",
            "gene_symbol",
            "--how",
            "left",
            "--out-tsv",
            str(out_tsv),
            "--constraint-version",
            "gnomad-v4.1",
        ],
        tmp_path,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert out_tsv.exists()
    assert out_tsv.stat().st_size > 0