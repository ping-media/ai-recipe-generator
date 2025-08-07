# Docker Deployment Guide for AI Recipe Generator

This guide explains how to deploy the AI Recipe Generator application using Docker on Linux servers.

## Prerequisites

- Docker installed on your Linux server
- Docker Compose installed
- Git (for manual deployment)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ping-media/ai-recipe-generator.git
cd ai-recipe-generator
```

### 2. Set Up Environment Variables

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

# FastAPI Configuration
HOST=0.0.0.0
PORT=8000
```

### 3. Deploy with Docker Compose

```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

Or manually:

```bash
# Build and start the application
docker-compose up --build -d

# Check the logs
docker-compose logs -f
```

## Docker Configuration

### Dockerfile

The Dockerfile clones the repository from GitHub and sets up the environment:

```dockerfile
# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

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

### Docker Compose

The `docker-compose.yml` file manages the application deployment:

```yaml
version: "3.8"

services:
  ai-recipe-generator:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX_NAME=${PINECONE_INDEX_NAME}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - HOST=0.0.0.0
      - PORT=8000
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - ./data:/app/data:ro
    networks:
      - recipe-network

networks:
  recipe-network:
    driver: bridge
```

## Deployment Options

### Option 1: Using the Deployment Script

The `deploy.sh` script automates the entire deployment process:

```bash
./deploy.sh
```

### Option 2: Manual Docker Commands

```bash
# Build the image
docker build -t ai-recipe-generator .

# Run the container
docker run -d \
  --name ai-recipe-generator \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/data:/app/data:ro \
  ai-recipe-generator
```

### Option 3: Docker Compose

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Environment Variables

| Variable              | Description               | Required              |
| --------------------- | ------------------------- | --------------------- |
| `MONGODB_URI`         | MongoDB connection string | Yes                   |
| `PINECONE_API_KEY`    | Pinecone API key          | Yes                   |
| `PINECONE_INDEX_NAME` | Pinecone index name       | Yes                   |
| `OPENAI_API_KEY`      | OpenAI API key            | Yes                   |
| `HOST`                | Application host          | No (default: 0.0.0.0) |
| `PORT`                | Application port          | No (default: 8000)    |

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

   # Change the port in docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

2. **Environment Variables Not Set**

   ```bash
   # Check if .env file exists
   ls -la .env

   # Create from example
   cp env.example .env
   ```

3. **Docker Build Fails**

   ```bash
   # Clean Docker cache
   docker system prune -a

   # Rebuild without cache
   docker-compose build --no-cache
   ```

4. **Application Won't Start**

   ```bash
   # Check container logs
   docker-compose logs ai-recipe-generator

   # Check if all environment variables are set
   docker-compose config
   ```

### Health Checks

The application includes health checks to ensure it's running properly:

```bash
# Check container health
docker ps

# Test health endpoint
curl http://localhost:8000/health
```

### Logs

```bash
# View real-time logs
docker-compose logs -f

# View logs for specific service
docker-compose logs ai-recipe-generator
```

## Production Deployment

For production deployment, consider:

1. **Use a reverse proxy** (nginx, traefik)
2. **Set up SSL/TLS certificates**
3. **Configure proper logging**
4. **Set up monitoring and alerting**
5. **Use Docker secrets for sensitive data**

### Example with Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
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
docker stats

# Monitor logs
docker-compose logs -f --tail=100

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Repository Information

- **GitHub Repository**: https://github.com/ping-media/ai-recipe-generator/
- **License**: MIT
- **Language**: Python 98.6%, Dockerfile 1.4%

## Support

For issues and questions:

1. Check the [GitHub repository](https://github.com/ping-media/ai-recipe-generator/)
2. Review the application logs
3. Ensure all environment variables are properly configured
4. Verify API keys are valid and have proper permissions
