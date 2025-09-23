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


def test_filter_runs(tmp_path: Path) -> None:
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