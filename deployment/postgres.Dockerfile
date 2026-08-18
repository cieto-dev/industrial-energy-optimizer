FROM postgres:17

# Install PostGIS + build deps, compile pgvector from release tarball, clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        postgresql-17-postgis-3 \
        postgis \
        build-essential \
        postgresql-server-dev-17 \
    && curl -fsSL https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.0.tar.gz \
        | tar -xz \
    && cd pgvector-0.8.0 \
    && make \
    && make install \
    && cd .. \
    && rm -rf pgvector-0.8.0 \
    && apt-get purge -y --auto-remove build-essential curl postgresql-server-dev-17 \
    && rm -rf /var/lib/apt/lists/*
