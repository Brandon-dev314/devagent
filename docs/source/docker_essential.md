# Docker Essentials for Developers

## What is Docker?

Docker is a platform for building, shipping, and running applications in containers. A container is a lightweight, standalone package that includes everything needed to run a piece of software: code, runtime, system tools, and libraries.

Unlike virtual machines, containers share the host OS kernel, making them much lighter and faster to start. A container typically starts in seconds, while a VM takes minutes.

## Key Concepts

### Images

A Docker image is a read-only template used to create containers. Think of it as a snapshot of a filesystem plus some metadata (what command to run, what ports to expose, etc.). Images are built from Dockerfiles and can be shared via registries like Docker Hub.

### Containers

A container is a running instance of an image. You can have multiple containers from the same image, each with its own state. Containers are ephemeral by default — when you stop them, any changes to the filesystem are lost unless you use volumes.

### Volumes

Volumes are Docker's mechanism for persisting data. They exist outside the container's filesystem and survive container restarts and removals. There are two types:

- Named volumes: Managed by Docker, stored in a Docker-controlled directory. Best for databases and persistent state.
- Bind mounts: Map a host directory directly into the container. Best for development (mount your source code for hot-reload).

### Networks

Docker creates isolated networks for containers. Containers on the same network can communicate using their container names as hostnames. Docker Compose automatically creates a network for all services defined in the compose file.

## Dockerfile Best Practices

### Multi-Stage Builds

Use multi-stage builds to create smaller, more secure images:

```dockerfile
# Stage 1: Build
FROM python:3.12 AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim
COPY --from=builder /install /usr/local
COPY ./app ./app
CMD ["python", "app/main.py"]
```

The final image only contains the runtime — no build tools, no cache files.

### Layer Caching

Docker caches each layer (each instruction in the Dockerfile). To maximize cache hits:

1. Put instructions that change rarely at the top (install OS packages)
2. Copy dependency files before source code (requirements.txt before your app)
3. Put instructions that change often at the bottom (COPY your code)

If a layer changes, all subsequent layers are invalidated and rebuilt.

### Security

Always run containers as non-root users:

```dockerfile
RUN useradd --system appuser
USER appuser
```

This limits the damage if an attacker exploits a vulnerability in your application.

## Docker Compose

Docker Compose defines multi-container applications in a single YAML file. Instead of running multiple `docker run` commands with complex flags, you define everything declaratively.

A typical compose file includes service definitions, networks, and volumes. Services can depend on each other, share networks, and mount volumes. The `depends_on` directive with health checks ensures services start in the correct order.

Common commands:
- `docker compose up -d` — Start all services in detached mode
- `docker compose down` — Stop and remove all services
- `docker compose logs -f` — Follow logs from all services
- `docker compose ps` — List running services
- `docker compose exec service_name bash` — Open a shell in a running service

## Health Checks

Health checks let Docker monitor if a service is actually working, not just running. Define them in your Dockerfile or compose file:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

Combined with `depends_on: condition: service_healthy`, this ensures your app doesn't try to connect to a database that isn't ready yet.