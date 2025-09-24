# Use a slim Python base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the entire project directory into the container
COPY . .

# Set the working directory to the package's location and install it
WORKDIR /app/parser-mcp
RUN pip install --no-cache-dir .[dev]

# Set the default command to start a shell when the container runs
CMD ["bash"]