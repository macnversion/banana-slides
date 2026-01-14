#!/bin/bash

# Banana Slides Backend Startup Script

echo "╔══════════════════════════════════════╗"
echo "║   🍌 Banana Slides API Server 🍌   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API keys."
    echo ""
fi

# Check if pixi is installed
if ! command -v pixi &> /dev/null; then
    echo "❌ Pixi is not installed."
    echo "📦 Please install Pixi first:"
    echo "   curl -fsSL https://pixi.sh/install.sh | bash"
    echo ""
    exit 1
fi

# Install dependencies using Pixi (run from project root)
echo "📥 Installing dependencies with Pixi..."
cd "$(dirname "$0")/.." || exit 1
pixi install

# Create instance folder if not exists
mkdir -p backend/instance
mkdir -p uploads

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting server..."
echo ""

# Run database migrations and start the application
cd backend || exit 1
pixi run alembic upgrade head && pixi run python app.py
