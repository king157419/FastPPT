#!/bin/bash

# FastPPT Quick Start Script

set -e

echo "========================================="
echo "FastPPT Docker Deployment"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Navigate to docker directory
cd "$(dirname "$0")"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit docker/.env with your API keys:"
    echo "   - DEEPSEEK_API_KEY"
    echo "   - DASHSCOPE_API_KEY"
    echo "   - Change default passwords"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Start services
echo "Starting FastPPT services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."
echo ""

# Check FastAPI
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✓ FastAPI Backend: Running (http://localhost:8000)"
else
    echo "✗ FastAPI Backend: Not responding"
fi

# Check PPTXGenJS
if curl -f http://localhost:3000/health &> /dev/null; then
    echo "✓ PPTXGenJS Service: Running (http://localhost:3000)"
else
    echo "✗ PPTXGenJS Service: Not responding"
fi

# Check PostgreSQL
if docker exec fastppt-postgres pg_isready -U fastppt &> /dev/null; then
    echo "✓ PostgreSQL: Running (localhost:5432)"
else
    echo "✗ PostgreSQL: Not responding"
fi

# Check Redis
if docker exec fastppt-redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2) ping &> /dev/null; then
    echo "✓ Redis: Running (localhost:6379)"
else
    echo "✗ Redis: Not responding"
fi

echo ""
echo "========================================="
echo "FastPPT is running!"
echo "========================================="
echo ""
echo "Access points:"
echo "  - API: http://localhost:8000"
echo "  - Health: http://localhost:8000/health"
echo "  - Metrics: http://localhost:8000/metrics"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
echo ""
