FROM python:3.12-slim

WORKDIR /app

# Copy the project files
COPY parser-mcp/pyproject.toml .
COPY README.md .
COPY parser-mcp/src/vep_parser_mcp/ ./src/vep_parser_mcp/

# Install the package and its dependencies
RUN pip install --no-cache-dir .[dev]

CMD ["bash"]