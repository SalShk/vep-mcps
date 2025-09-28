from __future__ import annotations

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Annotated, Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from pydantic import BaseModel
import yaml
import xxhash
import pandas as pd

console = Console()
app = typer.Typer(add_completion=False)

# -------- defaults via env so Docker runs can mount refs ----------
ENV_VEP = os.environ.get("VEP_EXEC", "vep")
ENV_VEP_DATA = os.environ.get("VEP_DATA_DIR", "/refs/vep/data")
ENV_VEP_PLUGINS = os.environ.get("VEP_PLUGINS_DIR", "/refs/vep/Plugins")
ENV_FASTA = os.environ.get("VEP_FASTA", f"{ENV_VEP_DATA}/Homo_sapiens.GRCh38.dna.primary_assembly.fa")

# ---------- simple manifest model ----------
class RunManifest(BaseModel):
    input_vcf: str
    output_tsv_gz: str
    vep_exec: str
    vep_cache_dir: str
    vep_plugins_dir: str
    reference_fasta: str
    args: List[str]
    versions: dict
    files_checksum: dict

def _sha256(path: Path) -> str:
    h = xxhash.xxh64()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _maybe_checksum(p: str | Path) -> Optional[str]:
    try:
        path = Path(p)
        return _sha256(path) if path.exists() and path.is_file() else None
    except Exception:
        return None

def _check_exists(path: str | Path, kind: str = "file", required: bool = True) -> bool:
    p = Path(path)
    ok = p.exists() and (p.is_dir() if kind == "dir" else p.is_file())
    if required and not ok:
        console.print(f"[red]Missing required {kind}: {p}[/red]")
        raise typer.Exit(code=2)
    return ok

def _build_dbnsfp_arg(dbnsfp_path: str) -> str:
    # Keep your original dbNSFP fields from the shell script (unchanged)
    fields = (
        "BayesDel_noAF_pred,ClinPred_pred,DANN_score,DEOGEN2_pred,FATHMM_pred,GERP++_RS,"
        "LRT_pred,M-CAP_pred,MetaLR_pred,MetaSVM_pred,MutationAssessor_pred,MutationTaster_pred,"
        "PROVEAN_pred,Polyphen2_HVAR_pred,PrimateAI_score,SIFT_pred,SiPhy_29way_logOdds,genename,"
        "rs_dbSNP,clinvar_MedGen_id,clinvar_OMIM_id,clinvar_Orphanet_id,clinvar_clnsig,clinvar_hgvs,"
        "clinvar_id,clinvar_review,clinvar_trait,clinvar_var_source,Eigen-phred_coding,GenoCanyon_score,"
        "fathmm-MKL_coding_pred,phastCons100way_vertebrate,phyloP100way_vertebrate"
    )
    return f"dbNSFP,{dbnsfp_path},{fields}"

@app.command()
def main(
    sample: Annotated[str, typer.Argument(help="Sample name label (used for outputs/logs).")],
    input_vcf: Annotated[Path, typer.Option("--input-vcf", "-i", exists=True, readable=True, help="Input VCF/BCF (gz OK).")],
    out_dir: Annotated[Path, typer.Option("--out-dir", "-o", help="Output directory.")] = Path("runner-mcp/out"),
    # refs/plugins
    vep_exec: Annotated[str, typer.Option("--vep-exec")] = ENV_VEP,
    vep_cache_dir: Annotated[str, typer.Option("--vep-cache-dir")] = ENV_VEP_DATA,
    vep_plugins_dir: Annotated[str, typer.Option("--vep-plugins-dir")] = ENV_VEP_PLUGINS,
    reference_fasta: Annotated[str, typer.Option("--reference-fasta")] = ENV_FASTA,
    # plugin datasets (required ones from your script)
    alpha_missense: Annotated[str, typer.Option("--alpha-missense")] = f"{ENV_VEP_DATA}/AlphaMissense_hg38.tsv.gz",
    ancestral_allele: Annotated[str, typer.Option("--ancestral-allele")] = f"{ENV_VEP_DATA}/human_ancestor.fa.gz",
    cadd_snv: Annotated[str, typer.Option("--cadd-snv")] = f"{ENV_VEP_DATA}/cadd_whole_genome_SNVs_v1.7.tsv.gz",
    cadd_indel: Annotated[str, typer.Option("--cadd-indel")] = f"{ENV_VEP_DATA}/cadd_gnomad.genomes.r4.0.indel.tsv.gz",
    clinvar_vcf: Annotated[str, typer.Option("--clinvar-vcf")] = f"{ENV_VEP_DATA}/clinvar.vcf.gz",
    dbnsfp: Annotated[str, typer.Option("--dbnsfp")] = f"{ENV_VEP_DATA}/dbNSFP4.9a_grch38.gz",
    primate_ai: Annotated[str, typer.Option("--primate-ai")] = f"{ENV_VEP_DATA}/PrimateAI_scores_v0.2_GRCh38_sorted.tsv.bgz",
    revel: Annotated[str, typer.Option("--revel")] = f"{ENV_VEP_DATA}/new_tabbed_revel_grch38.tsv.gz",
    spliceai_snv: Annotated[str, typer.Option("--spliceai-snv")] = f"{ENV_VEP_DATA}/spliceai_scores.raw.snv.hg38.vcf.gz",
    spliceai_indel: Annotated[str, typer.Option("--spliceai-indel")] = f"{ENV_VEP_DATA}/spliceai_scores.raw.indel.hg38.vcf.gz",
    splicevault: Annotated[str, typer.Option("--splicevault")] = f"{ENV_VEP_DATA}/SpliceVault_data_GRCh38.tsv.gz",
    loftee_conservation: Annotated[str, typer.Option("--loftee-conservation")] = f"{ENV_VEP_DATA}/phylocsf_gerp.sql",
    loftee_splice_dir: Annotated[str, typer.Option("--loftee-splice-dir")] = f"{ENV_VEP_PLUGINS_DIR}/loftee/splice_data",
    assembly: Annotated[str, typer.Option("--assembly")] = "GRCh38",
    species: Annotated[str, typer.Option("--species")] = "homo_sapiens",
    # behavior
    threads: Annotated[int, typer.Option("--threads")] = 1,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print command and exit.")] = False,
) -> None:
    """
    Run Ensembl VEP with a stable set of plugins/flags and emit a reproducible manifest.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_tsv_gz = out_dir / f"{sample}_vep_annotated.txt.gz"
    cmd_log = out_dir / f"{sample}_vep_command.log"
    stderr_log = out_dir / f"{sample}_vep_stderr.log"
    manifest_yml = out_dir / f"{sample}_vep_manifest.yml"

    # sanity of refs
    for p in [vep_cache_dir, vep_plugins_dir]:
        _check_exists(p, kind="dir", required=True)
    for p in [
        reference_fasta, alpha_missense, ancestral_allele, cadd_snv, cadd_indel, clinvar_vcf,
        dbnsfp, primate_ai, revel, spliceai_snv, spliceai_indel, splicevault, loftee_conservation
    ]:
        _check_exists(p, kind="file", required=True)

    console.print(Panel.fit(
        f"[bold]VEP Runner MCP[/bold]\n"
        f"sample: [cyan]{sample}[/cyan]\n"
        f"in: [cyan]{input_vcf}[/cyan]\n"
        f"out: [cyan]{out_tsv_gz}[/cyan]\n"
        f"cache: [cyan]{vep_cache_dir}[/cyan]\n"
        f"plugins: [cyan]{vep_plugins_dir}[/cyan]",
        title="vep-run", border_style="blue"
    ))

    # build command (mirrors your bash script)  :contentReference[oaicite:1]{index=1}
    args = [
        vep_exec,
        "--cache", "--offline",
        "--dir_cache", vep_cache_dir,
        "--dir_plugins", vep_plugins_dir,
        "--input_file", str(input_vcf),
        "--output_file", str(out_tsv_gz),
        "--species", species,
        "--assembly", assembly,
        "--tab", "--force_overwrite",
        "--fasta", reference_fasta,
        "--mane_select", "--check_existing",
        "--individual_zyg", "all",
        "--everything", "--safe",
        "--verbose",
        "--plugin", _build_dbnsfp_arg(dbnsfp),
        "--plugin", f"AlphaMissense,file={alpha_missense}",
        "--plugin", f"PrimateAI,{primate_ai}",
        "--plugin", f"SpliceAI,snv={spliceai_snv},indel={spliceai_indel}",
        "--plugin", f"LoF,loftee_path:{vep_plugins_dir}/loftee,gerp_file:false,conservation_file:{loftee_conservation},human_ancestor_fa:{ancestral_allele},splice_data_dir:{loftee_splice_dir}",
        "--plugin", f"SpliceVault,files={splicevault}",
        "--plugin", f"CADD,snv={cadd_snv},indels={cadd_indel}",
        "--plugin", f"REVEL,file={revel}",
    ]
    if threads and threads > 1:
        args += ["--fork", str(threads)]

    cmd_str = " ".join(str(a) for a in args)
    cmd_log.write_text(cmd_str + "\n")

    if dry_run:
        console.print("\n[bold yellow]--dry-run[/bold yellow] printing command and exiting:\n")
        console.print(cmd_str)
        raise typer.Exit(code=0)

    # execute
    console.log("[blue]$[/blue] " + cmd_str)
    with open(stderr_log, "w", encoding="utf-8") as err:
        proc = subprocess.run(args, stderr=err)
    if proc.returncode != 0:
        console.print(f"[red]VEP exited with code {proc.returncode}[/red]")
        raise typer.Exit(code=proc.returncode)

    # manifest
    versions = {
        "vep_exec": vep_exec,
        "python": sys.version.split()[0],
    }
    files_checksum = {
        "reference_fasta": _maybe_checksum(reference_fasta),
        "dbnsfp": _maybe_checksum(dbnsfp),
        "alpha_missense": _maybe_checksum(alpha_missense),
        "ancestral_allele": _maybe_checksum(ancestral_allele),
        "cadd_snv": _maybe_checksum(cadd_snv),
        "cadd_indel": _maybe_checksum(cadd_indel),
        "clinvar_vcf": _maybe_checksum(clinvar_vcf),
        "primate_ai": _maybe_checksum(primate_ai),
        "revel": _maybe_checksum(revel),
        "spliceai_snv": _maybe_checksum(spliceai_snv),
        "spliceai_indel": _maybe_checksum(spliceai_indel),
        "splicevault": _maybe_checksum(splicevault),
        "loftee_conservation": _maybe_checksum(loftee_conservation),
        "input_vcf": _maybe_checksum(input_vcf),
        "output_tsv_gz": _maybe_checksum(out_tsv_gz),
    }
    manifest = RunManifest(
        input_vcf=str(input_vcf),
        output_tsv_gz=str(out_tsv_gz),
        vep_exec=vep_exec,
        vep_cache_dir=vep_cache_dir,
        vep_plugins_dir=vep_plugins_dir,
        reference_fasta=reference_fasta,
        args=args,
        versions=versions,
        files_checksum=files_checksum,
    )
    with open(manifest_yml, "w", encoding="utf-8") as f:
        yaml.safe_dump(json.loads(manifest.model_dump_json()), f, sort_keys=False)

    console.print(Panel.fit(
        f"[green]VEP finished[/green]\n"
        f"out: [bold]{out_tsv_gz}[/bold]\n"
        f"stderr: {stderr_log}\n"
        f"manifest: {manifest_yml}",
        title="done", border_style="green"
    ))

def cli():
    typer.run(main)

if __name__ == "__main__":
    # Support: python -m vep_runner_mcp.cli.run --flags ...
    first = sys.argv[1] if len(sys.argv) > 1 else ""
    if first.startswith("-") or first == "":
        typer.run(main)
    else:
        app()
