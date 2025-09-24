from __future__ import annotations

from pathlib import Path
from typing import Annotated, List, Optional
import time
import typer
from rich.console import Console
from rich.panel import Panel
from shutil import which
import subprocess

app = typer.Typer(add_completion=False)
console = Console()


def _run(argv: List[str], title: str) -> float:
    """Run a CLI step with timing and rich logging; raises on non-zero exit."""
    console.log("[blue]$[/blue] " + " ".join(map(str, argv)))
    t0 = time.perf_counter()
    try:
        subprocess.run(argv, check=True)
    except subprocess.CalledProcessError as e:
        console.log(f"[red]Step failed ({title}) with exit code {e.returncode}[/red]")
        raise typer.Exit(code=e.returncode)
    dt = time.perf_counter() - t0
    console.log(f"[green]✓ {title}[/green] ([dim]{dt:.2f}s[/dim])")
    return dt


def _must_exist(cmd: str) -> None:
    if which(cmd) is None:
        console.log(f"[red]Missing required command in PATH: {cmd}[/red]")
        raise typer.Exit(code=127)


@app.command()
def main(
    in_tsv: Annotated[Path, typer.Option("-i", "--in-tsv", exists=True, readable=True, help="VEP TSV input")],
    constraint_tsv: Annotated[Path, typer.Option("-c", "--constraint-tsv", exists=True, readable=True, help="gnomAD constraint TSV(.gz)")],
    out_dir: Annotated[Path, typer.Option("-o", "--out-dir", help="Output directory")]=Path("parser-mcp/out"),
    keep_consequence: Annotated[str, typer.Option("--keep-consequence", help="Comma-separated consequences to keep")]="missense_variant,stop_gained",
    mane_only: Annotated[bool, typer.Option("--mane-only", help="Keep only MANE select transcripts")]=False,
    vep_cache_version: Annotated[str, typer.Option("--vep-cache-version")]="109",
    plugins_version: Annotated[str, typer.Option("--plugins-version")]="v1.0",
    merge_on: Annotated[str, typer.Option("--on", help="Join key: transcript|gene_symbol")]="transcript",
    merge_how: Annotated[str, typer.Option("--how", help="left|inner")]="left",
    constraint_version: Annotated[Optional[str], typer.Option("--constraint-version", help="Annotate result with constraint version")]=None,
    gzip_out: Annotated[bool, typer.Option("--gzip-out", help="Write outputs as .tsv.gz")]=False,
    skip_overview: Annotated[bool, typer.Option("--skip-overview", help="Skip final overview")]=False,
) -> None:
    """
    One-shot pipeline: filter → normalise → merge → (overview).
    Produces filtered.tsv[.gz], normalised.tsv[.gz], merged.tsv[.gz] in --out-dir.
    """
    # Ensure the sub-commands are actually available
    for cmd in [
        "vep-filter-consequence-mane",
        "vep-normalise-columns",
        "vep-merge-gnomad-constraint",
        "vep-overview",
    ]:
        if cmd == "vep-overview" and skip_overview:
            continue
        _must_exist(cmd)

    out_dir.mkdir(parents=True, exist_ok=True)

    def with_ext(name: str) -> Path:
        return out_dir / (f"{name}.tsv.gz" if gzip_out else f"{name}.tsv")

    filtered = with_ext("filtered")
    normalised = with_ext("normalised")
    merged = with_ext("merged")

    console.print(Panel.fit(
        f"[bold]VEP MCP Pipeline[/bold]\n"
        f"in: [cyan]{in_tsv}[/cyan]\n"
        f"constraint: [cyan]{constraint_tsv}[/cyan]\n"
        f"out dir: [cyan]{out_dir}[/cyan]",
        title="prepare-pipeline",
        border_style="blue",
    ))

    total = 0.0

    # 1) Filter
    argv = [
        "vep-filter-consequence-mane",
        "-i", str(in_tsv),
        "-o", str(filtered),
        "--keep-consequence", keep_consequence,
    ]
    if mane_only:
        argv.append("--mane-only")
    total += _run(argv, "filter")

    # 2) Normalise
    argv = [
        "vep-normalise-columns",
        "-i", str(filtered),
        "-o", str(normalised),
        "--vep-cache-version", vep_cache_version,
        "--plugins-version", plugins_version,
    ]
    total += _run(argv, "normalise")

    # 3) Merge
    argv = [
        "vep-merge-gnomad-constraint",
        "-i", str(normalised),
        "-c", str(constraint_tsv),
        "-o", str(merged),
        "--on", merge_on,
        "--how", merge_how,
    ]
    if constraint_version:
        argv += ["--constraint-version", constraint_version]
    total += _run(argv, "merge")

    # 4) Overview (optional)
    if not skip_overview:
        argv = ["vep-overview", "-i", str(merged)]
        total += _run(argv, "overview")

    console.print(Panel.fit(
        f"[green]Pipeline complete[/green] → [bold]{merged}[/bold]\n"
        f"filtered:  {filtered}\n"
        f"normalised: {normalised}\n"
        f"merged:     {merged}\n"
        f"[dim]elapsed ~{total:.2f}s[/dim]",
        title="done",
        border_style="green",
    ))

if __name__ == "__main__":
    # Support: python -m vep_parser_mcp.cli.filter_consequence_and_mane --in-tsv ...
    # Typer expects the subcommand name ("main"). If options come first, insert it.
    import sys
    if len(sys.argv) > 1 and sys.argv[1].startswith("-"):
        sys.argv.insert(1, "main")
    app()