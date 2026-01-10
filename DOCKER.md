# Docker Setup for ThreeDLLM

This guide explains how to run ThreeDLLM using Docker.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose (usually included with Docker Desktop)
- For GPU support: NVIDIA Docker runtime ([nvidia-docker](https://github.com/NVIDIA/nvidia-docker)

## Quick Start

### CPU-only (Default)

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Access the web interface
# Open http://localhost:8000 in your browser
```

### GPU Support

```bash
# Build and run with GPU
docker-compose -f docker-compose.gpu.yml up -d

# View logs
docker-compose -f docker-compose.gpu.yml logs -f
```

## Environment Variables

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API key:**
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DEVICE=auto  # or "cuda" for GPU, "cpu" for CPU-only
   ```

3. **The `.env` file is automatically loaded by docker-compose**

Alternatively, you can set environment variables when running:

```bash
OPENAI_API_KEY=your_key docker-compose up -d
```

**Note:** The `.env` file is gitignored and won't be committed to version control.

## Building Images

### CPU Image

```bash
docker build -t threedllm:latest .
```

### GPU Image

```bash
docker build -f Dockerfile.gpu -t threedllm:gpu .
```

## Running Containers

### Using Docker Compose (Recommended)

**CPU:**
```bash
docker-compose up -d
```

**GPU:**
```bash
docker-compose -f docker-compose.gpu.yml up -d
```

### Using Docker Directly

**CPU:**
```bash
docker run -d \
  --name threedllm \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -v $(pwd)/outputs:/app/outputs \
  threedllm:latest
```

**GPU:**
```bash
docker run -d \
  --name threedllm-gpu \
  --gpus all \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e DEVICE=cuda \
  -v $(pwd)/outputs:/app/outputs \
  threedllm:gpu
```

## Managing Containers

### View Logs

```bash
# Using docker-compose
docker-compose logs -f

# Using docker
docker logs -f threedllm
```

### Stop Container

```bash
# Using docker-compose
docker-compose down

# Using docker
docker stop threedllm
docker rm threedllm
```

### Restart Container

```bash
# Using docker-compose
docker-compose restart

# Using docker
docker restart threedllm
```

### Access Container Shell

```bash
docker exec -it threedllm bash
```

## Volumes

The Docker setup mounts:
- `./outputs` → `/app/outputs` - Generated 3D files
- `./frontend` → `/app/frontend` - Frontend files (read-only)

## Ports

- `8000` - API and web interface

To use a different port:

```bash
docker-compose up -d
# Edit docker-compose.yml to change "8000:8000" to "8080:8000"
```

## Health Checks

The container includes health checks. Check status:

```bash
docker ps
# Look for "healthy" status
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Check if port is already in use
lsof -i :8000
```

### GPU not working

1. Verify NVIDIA Docker runtime:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
   ```

2. Use GPU compose file:
   ```bash
   docker-compose -f docker-compose.gpu.yml up -d
   ```

### Out of memory

Increase Docker memory limit in Docker Desktop settings, or use CPU-only mode.

### Models downloading slowly

Shap-E models are downloaded on first use. This can take time. Check logs:

```bash
docker-compose logs -f
```

### API not accessible

1. Check container is running:
   ```bash
   docker ps
   ```

2. Check health:
   ```bash
   curl http://localhost:8000/api/health
   ```

3. Check firewall settings

## Production Deployment

For production, consider:

1. **Use specific image tags** instead of `latest`
2. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

3. **Use environment files** for secrets
4. **Enable HTTPS** with a reverse proxy (nginx, traefik)
5. **Set up logging** to external service
6. **Use volume mounts** for persistent data

## Building Custom Images

To customize the build:

```bash
# Edit Dockerfile
docker build -t threedllm:custom .

# Or with build args
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t threedllm:custom .
```

## Multi-Architecture Builds

Build for different platforms:

```bash
# Build for ARM64 (Apple Silicon, Raspberry Pi)
docker buildx build --platform linux/arm64 -t threedllm:arm64 .

# Build for AMD64
docker buildx build --platform linux/amd64 -t threedllm:amd64 .
```
