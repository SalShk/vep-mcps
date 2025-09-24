FROM python:3.12-slim

WORKDIR /app

# Copy everything from the project root
COPY . /app/

# Install the package
RUN cd parser-mcp && \
    pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir .[dev]

WORKDIR /app/parser-mcp
CMD ["bash"]