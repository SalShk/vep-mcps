#!/usr/bin/env python3
from __future__ import annotations
import os, sys, shlex, subprocess, re

def _print_version_and_exit() -> int:
    # Run `vep --help` and parse "ensembl-vep : X.Y"
    proc = subprocess.run(["vep", "--help"], capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    m = re.search(r"ensembl-vep\s*:\s*([0-9.]+)", out)
    if m:
        print(m.group(1))
        return 0
    # Fallback: just show the first ~20 lines of help
    sys.stderr.write(out.splitlines(True)[:20] and "".join(out.splitlines(True)[:20]))
    return 0 if proc.returncode == 0 else proc.returncode

def main() -> int:
    # If user asked for --version, emulate it
    if any(a in ("--version", "-V") for a in sys.argv[1:]):
        return _print_version_and_exit()

    # Otherwise pass everything straight to VEP (+ optional defaults)
    env_opts = os.environ.get("VEP_OPTS", "")
    argv = ["vep"] + (shlex.split(env_opts) if env_opts else []) + sys.argv[1:]
    sys.stderr.write("$ " + " ".join(shlex.quote(a) for a in argv) + "\n")
    sys.stderr.flush()
    try:
        return subprocess.call(argv)
    except KeyboardInterrupt:
        return 130

if __name__ == "__main__":
    sys.exit(main())
