# Troubleshooting Guide

## "3D generator is not available" Error

This error occurs when the Shap-E generator cannot be initialized. Here are common causes and solutions:

### 1. Shap-E Not Installed

**Symptoms:**
- Error: "3D generator is not available"
- Health check shows `generator_available: false`

**Solution:**
```bash
# In Docker container
docker exec -it threedllm bash
pip install git+https://github.com/openai/shap-e.git
pip install ipywidgets
```

Or rebuild the Docker image:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### 2. Missing Dependencies

**Symptoms:**
- Import errors in logs
- ModuleNotFoundError for ipywidgets

**Solution:**
Ensure all dependencies are installed:
```bash
pip install ipywidgets
pip install git+https://github.com/openai/shap-e.git
```

### 3. Check Container Logs

```bash
# View recent logs
docker-compose logs --tail=100 threedllm

# Check for import errors
docker-compose logs threedllm | grep -i "import\|error\|available"
```

### 4. Verify Installation Inside Container

```bash
# Enter container
docker exec -it threedllm bash

# Check if shap-e is installed
python -c "import shap_e; print('Shap-E installed')"

# Check if ipywidgets is installed
python -c "import ipywidgets; print('ipywidgets installed')"

# Test generator
python -c "from threedllm.generators.shap_e import ShapEGenerator; g = ShapEGenerator(); print('Available:', g.is_available())"
```

### 5. Rebuild from Scratch

If issues persist:

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi threedllm-threedllm

# Rebuild
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

### 6. Check Health Endpoint

```bash
# Check API health
curl http://localhost:8000/api/health

# Should return:
# {
#   "status": "healthy",
#   "version": "0.1.0",
#   "generator_available": true,
#   "vlm_available": true
# }
```

## Common Issues

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

### Out of Memory

```bash
# Increase Docker memory limit in Docker Desktop settings
# Or use CPU-only mode for smaller memory footprint
```

### Slow Model Downloads

Shap-E models download on first use. This can take several minutes. Check logs:
```bash
docker-compose logs -f threedllm
```

### VLM Not Available

This is expected if `OPENAI_API_KEY` is not set. VLM features will be disabled but generation will still work.

## Getting Help

1. Check container logs: `docker-compose logs threedllm`
2. Check health endpoint: `curl http://localhost:8000/api/health`
3. Verify installation inside container (see step 4 above)
4. Check Docker version: `docker --version`
5. Check disk space: `df -h`
