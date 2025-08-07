#!/bin/bash

# AI Recipe Generator - Simple Docker Deployment
# This script deploys the AI Recipe Generator using only Docker commands

set -e

echo "🚀 Starting AI Recipe Generator deployment with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "📝 Please edit .env file with your actual API keys and configuration."
        echo "   Required environment variables:"
        echo "   - MONGODB_URI"
        echo "   - PINECONE_API_KEY"
        echo "   - PINECONE_INDEX_NAME"
        echo "   - OPENAI_API_KEY"
        echo ""
        echo "   After editing .env, run this script again."
        exit 1
    else
        echo "❌ env.example file not found. Please create a .env file manually."
        exit 1
    fi
fi

# Create data directory if it doesn't exist
mkdir -p data

# Stop and remove existing container
echo "🛑 Stopping existing container..."
docker stop ai-recipe-generator 2>/dev/null || true
docker rm ai-recipe-generator 2>/dev/null || true

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t ai-recipe-generator .

# Run the container
echo "🚀 Starting the application..."
docker run -d \
    --name ai-recipe-generator \
    -p 8000:8000 \
    --env-file .env \
    -v $(pwd)/data:/app/data:ro \
    --restart unless-stopped \
    ai-recipe-generator

# Wait for the application to be ready
echo "⏳ Waiting for the application to be ready..."
sleep 15

# Check if the application is running
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Application is running successfully!"
    echo "🌐 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo "📊 API Root: http://localhost:8000/"
    echo ""
    echo "📚 Repository: https://github.com/ping-media/ai-recipe-generator/"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker logs -f ai-recipe-generator"
    echo "   Stop app: docker stop ai-recipe-generator"
    echo "   Start app: docker start ai-recipe-generator"
    echo "   Remove app: docker rm -f ai-recipe-generator"
else
    echo "❌ Application failed to start. Check logs with: docker logs ai-recipe-generator"
    exit 1
fi

echo "🎉 Deployment completed successfully!" 