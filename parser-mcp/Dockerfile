FROM python:3.12-slim

WORKDIR /app

COPY parser-mcp/pyproject.toml .
COPY parser-mcp/README.md .
COPY parser-mcp/src/vep_parser_mcp/ /app/src/vep_parser_mcp/
COPY tests/ /app/tests/

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir .

CMD ["bash"]