# Base: official VEP image (includes Perl, VEP, caches support, LOFTEE deps, etc.)
FROM ensemblorg/ensembl-vep:release_115.2

# We need Python for the tiny wrapper; install minimal deps
USER root
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m pip install "typer[all]>=0.9,<1.0" "rich>=13,<14"

# Add the wrapper and make it executable
WORKDIR /opt/vep_runner_mcp
COPY runner-mcp/src/vep_runner_mcp/cli/vep_runner.py /usr/local/bin/vep-runner
RUN chmod +x /usr/local/bin/vep-runner

# If you prefer dropping privileges and the base image has a 'vep' user:
# USER vep

# Our wrapper is the entrypoint; with no args it will show `vep --help`
ENTRYPOINT ["/usr/local/bin/vep-runner"]
# (no CMD needed; wrapper defaults to --help if no args)
