#!/bin/bash
# Setup script for Children's Video Content Evaluation System

echo "=================================================="
echo "   Children's Video Content Evaluation System"
echo "           Setup Script"
echo "=================================================="
echo ""

# Check Python
echo "📋 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python found: $(python3 --version)"
echo ""

# Check FFmpeg
echo "📋 Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Install it for video processing:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt-get install ffmpeg"
    echo ""
else
    echo "✅ FFmpeg found: $(ffmpeg -version | head -n 1)"
    echo ""
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Setup .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API key:"
    echo "   OPENAI_API_KEY=sk-your-api-key-here"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Check if API key is set
source .env 2>/dev/null
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-api-key-here" ]; then
    echo "⚠️  OpenAI API key not configured"
    echo "   Please edit .env and add your API key"
    echo ""
else
    echo "✅ OpenAI API key is configured"
    echo ""
fi

echo "=================================================="
echo "             Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. If needed, edit .env and add your OpenAI API key"
echo "  2. Run: python main.py"
echo ""
echo "For help, see: README_MAIN.md"
echo ""

