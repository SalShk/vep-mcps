FROM ensemblorg/ensembl-vep:release_115.2

# become root to install Python + certs (for rich)
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# add our thin wrapper
WORKDIR /opt/vep_runner_mcp
COPY runner-mcp/src/vep_runner_mcp/cli/vep_runner.py /usr/local/bin/vep-runner
RUN chmod +x /usr/local/bin/vep-runner

# default entrypoint: pass all args to `vep` via wrapper
ENTRYPOINT ["/usr/local/bin/vep-runner"]
# no CMD: whatever user supplies is forwarded to `vep`
