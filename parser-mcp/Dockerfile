FROM python:3.12-slim

WORKDIR /app

COPY parser-mcp/pyproject.toml /app/
COPY README.md /app/
COPY parser-mcp/src/vep_parser_mcp/ /app/src/vep_parser_mcp/
COPY tests/ /app/tests/
COPY schemas/ /app/schemas/

RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir .[dev] && \
    echo '#!/usr/local/bin/python3.12' > /usr/local/bin/vep-filter-consequence-mane && \
    echo 'import typer' >> /usr/local/bin/vep-filter-consequence-mane && \
    echo 'from vep_parser_mcp.cli.filter_consequence_and_mane import main' >> /usr/local/bin/vep-filter-consequence-mane && \
    echo 'if __name__ == "__main__":' >> /usr/local/bin/vep-filter-consequence-mane && \
    echo '    typer.run(main)' >> /usr/local/bin/vep-filter-consequence-mane && \
    chmod +x /usr/local/bin/vep-filter-consequence-mane && \
    echo '#!/usr/local/bin/python3.12' > /usr/local/bin/vep-normalise-columns && \
    echo 'import typer' >> /usr/local/bin/vep-normalise-columns && \
    echo 'from vep_parser_mcp.cli.normalise_columns import main' >> /usr/local/bin/vep-normalise-columns && \
    echo 'if __name__ == "__main__":' >> /usr/local/bin/vep-normalise-columns && \
    echo '    typer.run(main)' >> /usr/local/bin/vep-normalise-columns && \
    chmod +x /usr/local/bin/vep-normalise-columns && \
    echo '#!/usr/local/bin/python3.12' > /usr/local/bin/vep-merge-gnomad-constraint && \
    echo 'import typer' >> /usr/local/bin/vep-merge-gnomad-constraint && \
    echo 'from vep_parser_mcp.cli.merge_gnomad_constraint import main' >> /usr/local/bin/vep-merge-gnomad-constraint && \
    echo 'if __name__ == "__main__":' >> /usr/local/bin/vep-merge-gnomad-constraint && \
    echo '    typer.run(main)' >> /usr/local/bin/vep-merge-gnomad-constraint && \
    chmod +x /usr/local/bin/vep-merge-gnomad-constraint

CMD ["bash"]