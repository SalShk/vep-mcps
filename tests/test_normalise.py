import subprocess
from pathlib import Path
import pytest

IMAGE = "vep-parser-mcp:0.1.0"
TESTS = Path("/workspaces/vep-mcps/tests/data")


def run_docker(args: list[str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
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


def test_normalise_runs(tmp_path: Path) -> None:
    # Run filter step to generate input
    filtered_tsv = tmp_path / "filtered.tsv"
    result_filter = run_docker(
        [
            "vep-filter-consequence-mane",
            "--in-tsv",
            str(TESTS / "tiny.vep.tsv"),
            "--out-tsv",
            str(filtered_tsv),
            "--keep-consequence",
            "missense_variant,stop_gained",
        ],
        tmp_path,
    )
    assert result_filter.returncode == 0, f"Filter failed: {result_filter.stderr}"
    assert filtered_tsv.exists()

    out_tsv = tmp_path / "normalised.tsv"
    result = run_docker(
        [
            "vep-normalise-columns",
            "--in-tsv",
            str(filtered_tsv),
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
    head = out_tsv.read_text().splitlines()[0]
    assert "vep_cache_version" in head and "plugins_version" in head