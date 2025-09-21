FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy project metadata + source
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY schemas/ /app/schemas/

# install the package into the image
RUN pip install --no-cache-dir hatchling && python -m pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
