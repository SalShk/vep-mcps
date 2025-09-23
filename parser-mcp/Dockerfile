FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/
COPY ../README.md /app/
COPY src/vep_parser_mcp/ /app/src/vep_parser_mcp/
COPY ../tests/ /app/tests/
COPY scripts/ /app/scripts/
COPY ../schemas/ /app/schemas/

RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir .[dev] && \
    cp /app/scripts/vep-filter-consequence-mane /usr/local/bin/vep-filter-consequence-mane && \
    cp /app/scripts/vep-normalise-columns /usr/local/bin/vep-normalise-columns && \
    cp /app/scripts/vep-merge-gnomad-constraint /usr/local/bin/vep-merge-gnomad-constraint && \
    chmod +x /usr/local/bin/vep-filter-consequence-mane && \
    chmod +x /usr/local/bin/vep-normalise-columns && \
    chmod +x /usr/local/bin/vep-merge-gnomad-constraint

CMD ["bash"]