#!/usr/bin/env python3
from __future__ import annotations
import os
import shlex
import subprocess
from typing import List

import typer
from rich.console import Console

# Allow unknown options & extra args so we can forward everything to `vep`
app = typer.Typer(
    add_completion=False,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
console = Console()


@app.callback()
def main(ctx: typer.Context, args: List[str] = typer.Argument(None)) -> None:
    """
    Thin wrapper around `vep` inside the container.
    Everything after `vep-runner ...` is forwarded to `vep`.
    If nothing is provided, defaults to `vep --help`.
    """
    env_defaults = os.environ.get("VEP_OPTS", "")
    argv = ["vep"]
    if env_defaults.strip():
        argv += shlex.split(env_defaults)

    argv += (args if args else ["--help"])

    console.log("[blue]$[/blue] " + " ".join(shlex.quote(a) for a in argv))
    try:
        subprocess.run(argv, check=True)
    except subprocess.CalledProcessError as e:
        raise typer.Exit(e.returncode)


if __name__ == "__main__":
    app()
