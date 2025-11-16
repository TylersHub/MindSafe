"""
Flask API for Children's Video Content Evaluator

Endpoints:
- GET /evaluate - Evaluate a YouTube video and return results
- POST /evaluate - Process video (placeholder for future use)
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))
sys.path.insert(0, str(PROJECT_ROOT / "video_data_extraction"))

from evaluation.evaluate_video import evaluate_video, save_results

app = Flask(__name__)


def extract_video_data(youtube_url: str, output_dir: Path) -> dict:
    """
    Extract video data from YouTube URL.
    
    Args:
        youtube_url: YouTube video URL
        output_dir: Directory to save extracted data
        
    Returns:
        Dictionary with extraction results
    """
    from video_data_extraction.main import process_youtube_video
    
    print(f"[API] Extracting video data from: {youtube_url}")
    result = process_youtube_video(
        youtube_url,
        str(output_dir),
        use_chunked_processing=False,  # FAST MODE: avoid visual LLM path
        segment_duration=30.0,
        frames_per_segment=20,
        audio_chunk_duration=60.0,
    )
    
    return result


def evaluate_extracted_video(output_dir: Path, child_age: float, api_key: str | None) -> dict:
    """
    Evaluate extracted video content.
    
    Args:
        output_dir: Directory containing extracted video data
        child_age: Age of child in years
        api_key: (unused in fast mode; kept for future LLM-enabled mode)
        
    Returns:
        Dictionary with evaluation results
    """
    video_path = output_dir / "video_with_audio.mp4"
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    print(f"[API] Evaluating video for age {child_age}...")

    # Run evaluation in FAST MODE (no LLM, no heavy motion analysis)
    results = evaluate_video(
        video_path=str(video_path),
        child_age=child_age,
        llm_client=None,
        outputs_dir=str(output_dir),
        compute_motion=False,
    )
    
    # Save results
    results_path = output_dir / "evaluation_results.json"
    save_results(results, str(results_path))
    print(f"[API] Results saved to: {results_path}")
    
    return results


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Children's Video Content Evaluator API",
        "version": "1.0.0"
    }), 200


@app.route('/evaluate', methods=['GET'])
def evaluate_get():
    """
    GET endpoint to evaluate a YouTube video.
    
    Query Parameters:
        - url (optional): YouTube video URL. If not provided, uses existing video in outputs folder
        - age (required): Child's age in years
        
    Returns:
        JSON with evaluation results including:
        - dev_score: Development score (0-100)
        - brainrot_index: Brainrot index (0-100)
        - dimension_scores: Scores for each dimension
        - metrics: Detailed metrics
        - recommendations: Age-appropriate recommendations
    """
    try:
        # Get query parameters
        youtube_url = request.args.get('url', '').strip()
        age_str = request.args.get('age')
        
        # Determine if we should use existing data
        use_existing = not youtube_url  # If no URL provided, use existing data
            
        if not age_str:
            return jsonify({
                "error": "Missing required parameter: age",
                "message": "Please provide child's age in years"
            }), 400
        
        # Parse age
        try:
            child_age = float(age_str)
            if child_age < 0 or child_age > 18:
                return jsonify({
                    "error": "Invalid age",
                    "message": "Age must be between 0 and 18"
                }), 400
        except ValueError:
            return jsonify({
                "error": "Invalid age format",
                "message": "Age must be a number (e.g., 4 or 4.5)"
            }), 400
        
        # API key is optional in fast mode (LLM disabled by default)
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Determine output directory
        if use_existing:
            # Use hardcoded outputs directory with existing video
            output_dir = PROJECT_ROOT / "outputs"
            temp_dir = None
            print(f"[API] Using existing video data from: {output_dir}")
        else:
            # Create temporary directory for new video
            temp_dir = Path(tempfile.mkdtemp(prefix="video_eval_"))
            output_dir = temp_dir
            print(f"[API] Created temporary directory: {output_dir}")
        
        try:
            # Step 1: Extract video data (only if URL provided)
            if not use_existing:
                print(f"[API] Starting video extraction for: {youtube_url}")
                extraction_result = extract_video_data(youtube_url, output_dir)
                print(f"[API] Video extraction complete")
            else:
                print(f"[API] Skipping extraction, using existing data in outputs/")
            
            # Step 2: Evaluate video
            print(f"[API] Starting evaluation for age {child_age}")
            results = evaluate_extracted_video(output_dir, child_age, api_key)
            print(f"[API] Evaluation complete")
            
            # Return results
            return jsonify(results), 200
            
        finally:
            # Clean up temporary directory (only if we created one)
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir)
                print(f"[API] Cleaned up temporary directory: {temp_dir}")
    
    except FileNotFoundError as e:
        return jsonify({
            "error": "File not found",
            "message": str(e)
        }), 404
    
    except Exception as e:
        print(f"[API] Error: {str(e)}")
        return jsonify({
            "error": "Evaluation failed",
            "message": str(e)
        }), 500


@app.route('/evaluate', methods=['POST'])
def evaluate_post():
    """
    POST endpoint for video evaluation (placeholder for future implementation).
    
    Expected JSON body:
        {
            "url": "YouTube video URL",
            "age": 4.5,
            "options": {
                "skip_extraction": false,
                "detailed_analysis": true
            }
        }
    
    Returns:
        JSON with evaluation results
    """
    return jsonify({
        "error": "Not implemented",
        "message": "POST endpoint is not yet implemented. Please use GET /evaluate for now."
    }), 501


@app.route('/evaluate/<video_id>', methods=['GET'])
def get_evaluation_by_id(video_id):
    """
    Get cached evaluation results by video ID (future feature).
    
    Args:
        video_id: Unique identifier for the evaluated video
        
    Returns:
        JSON with cached evaluation results
    """
    return jsonify({
        "error": "Not implemented",
        "message": "Cached results retrieval is not yet implemented."
    }), 501


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == '__main__':
    # Run the Flask app
    print("=" * 70)
    print("  Children's Video Content Evaluator API")
    print("=" * 70)
    print("\nAPI Endpoints:")
    print("  GET  /health              - Health check")
    print("  GET  /evaluate?age=...    - Evaluate video (requires age, url optional)")
    print("  POST /evaluate            - Placeholder (not yet implemented)")
    print("\nExample usage:")
    print("  # With YouTube URL (download new video):")
    print('  curl "http://localhost:5001/evaluate?url=YOUTUBE_URL&age=4"')
    print()
    print("  # Without URL (use existing video in outputs/):")
    print('  curl "http://localhost:5001/evaluate?age=4"')
    print("\nStarting server...")
    print("=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)

