FROM python:3.12-slim

LABEL maintainer="Zichao Zeng"
LABEL description="PyiTOL - iTOL phylogenetic tree visualization automation"

WORKDIR /app

# Stream container logs in real time (no buffering) for `docker logs` / orchestrators
ENV PYTHONUNBUFFERED=1

# Install system dependencies for scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir .

# Create non-root user for security
RUN useradd --create-home pyitol
USER pyitol
WORKDIR /home/pyitol

ENTRYPOINT ["pyitol"]
CMD ["--help"]
