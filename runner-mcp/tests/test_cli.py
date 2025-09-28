import subprocess

def test_help():
    assert subprocess.call(["python", "-m", "vep_runner_mcp.cli.run", "--help"]) == 0

def test_dry_run(tmp_path):
    fake = tmp_path / "x.vcf.gz"
    fake.write_text("")  # only existence is checked in dry-run? we check refs; so skip
    # For dry-run we must pass existing paths; point them to tmp dir
    outdir = tmp_path / "out"
    outdir.mkdir()

    cmd = [
        "python", "-m", "vep_runner_mcp.cli.run", "SAMPLE",
        "-i", str(fake),
        "-o", str(outdir),
        "--vep-cache-dir", str(tmp_path),
        "--vep-plugins-dir", str(tmp_path),
        "--reference-fasta", str(fake),
        "--alpha-missense", str(fake),
        "--ancestral-allele", str(fake),
        "--cadd-snv", str(fake),
        "--cadd-indel", str(fake),
        "--clinvar-vcf", str(fake),
        "--dbnsfp", str(fake),
        "--primate-ai", str(fake),
        "--revel", str(fake),
        "--spliceai-snv", str(fake),
        "--spliceai-indel", str(fake),
        "--splicevault", str(fake),
        "--loftee-conservation", str(fake),
        "--loftee-splice-dir", str(tmp_path),
        "--dry-run",
    ]
    # Should exit 0 and print the command without executing VEP
    assert subprocess.call(cmd) == 0
