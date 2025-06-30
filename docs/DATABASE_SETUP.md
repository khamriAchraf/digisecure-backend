# Setting Up PostgreSQL 17 with Docker and Enabling pgaudit

This guide will help you run a PostgreSQL 17 database in a Docker container, install the `pgaudit` extension, and enable it for enhanced auditing.

---

## 1. Start a PostgreSQL 17 Docker Container

You can use the official PostgreSQL Docker image. If you want to persist data, create a volume or bind-mount a host directory.

## 2. Install the `pgaudit` Extension

The official PostgreSQL Docker image does not include `pgaudit` by default. You need to install it. The easiest way is to use a Dockerfile to build a custom image:

```dockerfile
# Dockerfile
FROM postgres:17

RUN apt-get update \
    && apt-get install -y postgresql-17-pgaudit \
    && rm -rf /var/lib/apt/lists/*
```

Build and run your custom image:

```bash
docker build -t my-postgres-pgaudit .
docker run --name my-postgres -e POSTGRES_PASSWORD=mysecretpassword -d my-postgres-pgaudit
```

---

## 3. Enable `pgaudit` in PostgreSQL

You need to update the `postgresql.conf` file to load the `pgaudit` extension and configure its settings.

### a. Edit `postgresql.conf`

You can do this by either:
- Mounting a custom `postgresql.conf` file, or
- Using Docker's `-c` flag to set parameters at runtime, or
- Executing SQL commands after the container starts.

**Key settings to add or modify:**

```conf
shared_preload_libraries = 'pgaudit'
pgaudit.log = 'read, write, ddl'
pgaudit.log_level = 'log'
pgaudit.log_catalog = off
```

**If you want to mount a custom config:**

1. Copy the default config from the container:
   ```bash
   docker cp my-postgres:/var/lib/postgresql/data/postgresql.conf ./postgresql.conf
   ```
2. Edit `postgresql.conf` as above.
3. Start the container with:
   ```bash
   docker run --name my-postgres -e POSTGRES_PASSWORD=mysecretpassword \
     -v $(pwd)/postgresql.conf:/var/lib/postgresql/data/postgresql.conf \
     -d my-postgres-pgaudit
   ```

**Or, use the `-c` flag:**

```bash
docker run --name my-postgres -e POSTGRES_PASSWORD=mysecretpassword \
  -d my-postgres-pgaudit \
  -c shared_preload_libraries=pgaudit \
  -c pgaudit.log=all \
  -c pgaudit.log_level=log
```

---

## 4. Create the Extension in Your Database

After the container is running, connect to the database and run:

```sql
CREATE EXTENSION pgaudit;
```

You can do this with:

```bash
docker exec -it my-postgres psql -U postgres -c "CREATE EXTENSION pgaudit;"
```

---

## 5. Verify `pgaudit` is Working

Check the logs or run:

```sql
SHOW shared_preload_libraries;
SHOW pgaudit.log;
```

---

