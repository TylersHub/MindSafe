#!/bin/bash
# Quick system test script

echo "=================================="
echo "Testing Children's Video Evaluator"
echo "=================================="
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Activating virtual environment..."
    source venv/bin/activate
fi

# Check if outputs exist
if [ -f "outputs/video_with_audio.mp4" ]; then
    echo "✅ Test video found"
    echo ""
    echo "Running quick evaluation test..."
    echo ""
    
    # Run evaluation on existing data
    python main.py --url "https://youtube.com/watch?v=test" --age 4 --skip-extraction
    
    echo ""
    echo "✅ System test complete!"
else
    echo "❌ No test video found in outputs/"
    echo ""
    echo "To test the system:"
    echo "1. Run with a real YouTube URL:"
    echo "   python main.py --url 'YOUTUBE_URL' --age 4"
    echo ""
    echo "Or copy test data:"
    echo "   cp -r video_data_extraction/outputs/* outputs/"
    echo "   ./test_system.sh"
fi

