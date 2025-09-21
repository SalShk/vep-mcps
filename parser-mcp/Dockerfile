FROM python:3.12-slim

# system deps for pandas, compressed I/O
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir hatchling && python -m pip install --no-cache-dir .

COPY src/ /app/src/
COPY schemas/ /app/schemas/
COPY tests/ /app/tests/

ENV PYTHONUNBUFFERED=1
# Example usage:
# docker run --rm -v $PWD:/wd -w /wd vep-parser-mcp \
#   vep-filter-consequence-mane --in-tsv tests/data/tiny.vep.tsv.gz --out-tsv out.tsv.gz --keep-consequence missense_variant

