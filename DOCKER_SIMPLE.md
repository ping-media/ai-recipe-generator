# Simple Docker Deployment Guide

This guide shows how to deploy the AI Recipe Generator using only Docker commands, without docker-compose.

## Prerequisites

- Docker installed on your Linux server
- Git (for manual deployment)

## Quick Start

### 1. Set Up Environment Variables

Create a `.env` file based on the example:

```bash
cp env.example .env
```

Edit the `.env` file with your actual API keys:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/recipe_db?retryWrites=true&w=majority

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=recipes-db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
```

### 2. Deploy with Simple Docker Commands

#### Option A: Using the Deployment Script

```bash
# Make the script executable
chmod +x deploy-docker.sh

# Run the deployment
./deploy-docker.sh
```

#### Option B: Manual Docker Commands

```bash
# Build the Docker image
docker build -t ai-recipe-generator .

# Run the container
docker run -d \
  --name ai-recipe-generator \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data:ro \
  --restart unless-stopped \
  ai-recipe-generator
```

## Docker Commands Reference

### Build the Image

```bash
docker build -t ai-recipe-generator .
```

### Run the Container

```bash
docker run -d \
  --name ai-recipe-generator \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data:ro \
  --restart unless-stopped \
  ai-recipe-generator
```

### Manage the Container

```bash
# View logs
docker logs -f ai-recipe-generator

# Stop the container
docker stop ai-recipe-generator

# Start the container
docker start ai-recipe-generator

# Remove the container
docker rm -f ai-recipe-generator

# Check container status
docker ps

# Check container health
docker inspect ai-recipe-generator | grep Health -A 10
```

### Environment Variables

You can also pass environment variables directly:

```bash
docker run -d \
  --name ai-recipe-generator \
  -p 8000:8000 \
  -e MONGODB_URI="your_mongodb_uri" \
  -e PINECONE_API_KEY="your_pinecone_key" \
  -e PINECONE_INDEX_NAME="recipes-db" \
  -e OPENAI_API_KEY="your_openai_key" \
  -v $(pwd)/data:/app/data:ro \
  --restart unless-stopped \
  ai-recipe-generator
```

## Dockerfile Details

The Dockerfile is self-contained and includes:

- **Base Image**: Python 3.11 slim
- **System Dependencies**: gcc, g++, build-essential, curl, git
- **Repository**: Clones from https://github.com/ping-media/ai-recipe-generator/
- **Security**: Runs as non-root user
- **Health Check**: Monitors application status
- **Port**: Exposes port 8000

```dockerfile
# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        build-essential \
        curl \
        git \
        && rm -rf /var/lib/apt/lists/*

# Clone the repository from GitHub
RUN git clone https://github.com/ping-media/ai-recipe-generator.git .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## API Endpoints

Once deployed, the application will be available at:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **API Root**: http://localhost:8000/

## Troubleshooting

### Common Issues

1. **Port Already in Use**

   ```bash
   # Check what's using port 8000
   sudo netstat -tulpn | grep :8000

   # Use a different port
   docker run -d \
     --name ai-recipe-generator \
     -p 8001:8000 \  # Use port 8001 instead
     --env-file .env \
     ai-recipe-generator
   ```

2. **Container Won't Start**

   ```bash
   # Check container logs
   docker logs ai-recipe-generator

   # Check if environment variables are set
   docker exec ai-recipe-generator env | grep -E "(MONGODB|PINECONE|OPENAI)"
   ```

3. **Build Fails**

   ```bash
   # Clean Docker cache
   docker system prune -a

   # Rebuild without cache
   docker build --no-cache -t ai-recipe-generator .
   ```

### Health Checks

```bash
# Check if container is healthy
docker ps

# Test health endpoint
curl http://localhost:8000/health

# Check container health status
docker inspect ai-recipe-generator | grep Health -A 10
```

### Logs

```bash
# View real-time logs
docker logs -f ai-recipe-generator

# View last 100 lines
docker logs --tail=100 ai-recipe-generator
```

## Production Deployment

For production, consider these additional options:

```bash
# Run with resource limits
docker run -d \
  --name ai-recipe-generator \
  -p 8000:8000 \
  --env-file .env \
  --memory=2g \
  --cpus=1.0 \
  --restart=always \
  ai-recipe-generator

# Run with custom network
docker network create recipe-network
docker run -d \
  --name ai-recipe-generator \
  --network recipe-network \
  -p 8000:8000 \
  --env-file .env \
  ai-recipe-generator
```

## Security Considerations

1. **Never commit `.env` files** to version control
2. **Use Docker secrets** for production deployments
3. **Run containers as non-root user** (already configured)
4. **Regularly update base images**
5. **Scan images for vulnerabilities**

## Monitoring

```bash
# Check resource usage
docker stats ai-recipe-generator

# Monitor logs
docker logs -f --tail=100 ai-recipe-generator

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Repository Information

- **GitHub Repository**: https://github.com/ping-media/ai-recipe-generator/
- **License**: MIT
- **Language**: Python 98.6%, Dockerfile 1.4%
