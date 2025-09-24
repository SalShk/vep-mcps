FROM python:3.12-slim

WORKDIR /app

# Copy the entire project directory into the container
COPY parser-mcp ./parser-mcp/
COPY README.md .
COPY requirements.txt .
COPY schemas ./schemas/
COPY tests ./tests/

# Set the working directory to the package's location and install it
WORKDIR /app/parser-mcp
RUN pip install --no-cache-dir .[dev]

# Set the default command to start a shell when the container runs
CMD ["bash"]