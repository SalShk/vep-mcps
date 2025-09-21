from __future__ import annotations

import json
from typing import Any

import typer

app = typer.Typer(add_completion=False)


@app.callback()
def _main() -> None:
    """
    Overview tool for the VEP Parsing MCP.
    Emits a JSON object describing available tools, their params, and I/O schemas.
    """
    return None


@app.command("show")
def show(
    pretty: bool = typer.Option(True, "--pretty/--no-pretty", help="Pretty-print JSON"),
) -> None:
    plan: dict[str, Any] = {
        "name": "vep-parsing-mcp",
        "schemas": {
            "VEP_RAW": "schemas/VEP_RAW.schema.json",
            "ANNOTATION_NORMALISED": "schemas/ANNOTATION_NORMALISED.schema.json",
            "GNOMAD_CONSTRAINT": "schemas/GNOMAD_CONSTRAINT.schema.json",
        },
        "tools": [
            {
                "name": "vep-filter-consequence-mane",
                "params": {
                    "in-tsv": "str (VEP_RAW; .tsv or .tsv.gz)",
                    "out-tsv": "str (VEP_RAW; .tsv or .tsv.gz)",
                    "keep-consequence": "list[str]",
                    "require-canonical": "bool",
                    "require-mane": "bool",
                },
                "input_schema": "VEP_RAW",
                "output_schema": "VEP_RAW",
            },
            {
                "name": "vep-normalise-columns",
                "params": {
                    "in-tsv": "str (VEP_RAW or filtered)",
                    "out-tsv": "str (ANNOTATION_NORMALISED)",
                    "vep-cache-version": "str (optional)",
                    "plugins-version": "str (optional)",
                },
                "input_schema": "VEP_RAW",
                "output_schema": "ANNOTATION_NORMALISED",
            },
            {
                "name": "vep-merge-gnomad-constraint",
                "params": {
                    "in-tsv": "str (ANNOTATION_NORMALISED)",
                    "constraint-tsv": "str (GNOMAD_CONSTRAINT TSV/TSV.GZ)",
                    "on": "str ['gene_symbol','transcript']",
                    "how": "str ['left','inner']",
                    "out-tsv": "str",
                    "constraint-version": "str (optional provenance tag, e.g. gnomad-v4.1)",
                },
                "input_schema": "ANNOTATION_NORMALISED",
                "output_schema": "ANNOTATION_NORMALISED",
            },
        ],
        "suggested_order": [
            "vep-filter-consequence-mane",
            "vep-normalise-columns",
            "vep-merge-gnomad-constraint",
        ],
    }
    typer.echo(
        json.dumps(
            plan,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
        )
    )


if __name__ == "__main__":
    app()
