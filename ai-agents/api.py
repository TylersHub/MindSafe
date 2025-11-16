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
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("[WARN] Supabase not configured. Caching disabled.")

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
    
    # Save results locally
    results_path = output_dir / "evaluation_results.json"
    save_results(results, str(results_path))
    print(f"[API] Results saved to: {results_path}")
    
    return results


def get_cached_evaluation(video_url: str) -> dict | None:
    """
    Return cached evaluation from Supabase if it exists, else None.
    Uses table: video_eval, primary key: video_path (text).
    """
    if supabase is None:
        return None

    try:
        resp = (
            supabase.table("video_eval")
            .select("*")
            .eq("video_path", video_url)
            .limit(1)
            .execute()
        )

        if not resp.data:
            return None

        row = resp.data[0]

        cached = {
            "video_path": row.get("video_path"),
            "child_age": row.get("child_age"),
            "age_band": row.get("age_band"),
            "age_band_name": row.get("age_band_name"),
            "duration_seconds": row.get("duration_seconds"),
            "duration_minutes": row.get("duration_minutes"),
            "dev_score": row.get("dev_score"),
            "dev_interpretation": row.get("dev_interpretation"),
            "brainrot_index": row.get("brainrot_index"),
            "brainrot_interpretation": row.get("brainrot_interpretation"),
            "overall_recommendation": row.get("overall_recommendation"),
            "dimension_scores": row.get("dimension_scores"),
            "metrics": row.get("metrics"),
            "strengths": row.get("strengths"),
            "concerns": row.get("concerns"),
            "recommendations": row.get("recommendations"),
        }
        print("[API] Cache hit in Supabase for", video_url)
        return cached

    except Exception as e:
        print(f"[API] Supabase cache lookup failed: {e}")
        return None


def save_evaluation_to_supabase(video_url: str, child_age: float, results: dict) -> None:
    """
    Save / upsert evaluation results into Supabase table `video_eval`.
    video_path is the primary key.
    """
    if supabase is None:
        return

    try:
        # Unpack nested structures from evaluation output
        metadata = results.get("metadata", {}) or {}
        overall_scores = results.get("overall_scores", {}) or {}
        interpretations = results.get("interpretations", {}) or {}
        dimension_scores = results.get("dimension_scores")
        raw_metrics = results.get("raw_metrics")
        recs = results.get("recommendations", {}) or {}

        # Build a simple recommendations list (separate from strengths/concerns)
        recommendations_list: list[str] = []
        overall_text = interpretations.get("overall")
        if overall_text:
            recommendations_list.append(overall_text)

        payload = {
            # Primary key
            "video_path": video_url,
            # Core metadata
            "child_age": metadata.get("child_age", child_age),
            "age_band": metadata.get("age_band"),
            # DB column is age_band_name, we map from age_band_label in metadata
            "age_band_name": metadata.get("age_band_label"),
            "duration_seconds": metadata.get("duration_seconds"),
            "duration_minutes": metadata.get("duration_minutes"),
            # Overall scores
            "dev_score": overall_scores.get("development_score"),
            "dev_interpretation": interpretations.get("developmental"),
            "brainrot_index": overall_scores.get("brainrot_index"),
            "brainrot_interpretation": interpretations.get("brainrot"),
            "overall_recommendation": interpretations.get("overall"),
            # JSON fields
            "dimension_scores": dimension_scores,
            "metrics": raw_metrics,
            # Recommendation breakdown
            "strengths": recs.get("strengths"),
            "concerns": recs.get("concerns"),
            "recommendations": recommendations_list,
        }

        (
            supabase
            .table("video_eval")
            .upsert(payload, on_conflict="video_path")
            .execute()
        )

        print("[API] Saved evaluation to Supabase for", video_url)

    except Exception as e:
        print(f"[API] Supabase cache save failed: {e}")


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

        # If URL provided, first check Supabase cache
        if youtube_url:
            cached = get_cached_evaluation(youtube_url)
            if cached is not None:
                return jsonify(cached), 200
            
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

            # Step 3: Save results to Supabase cache if URL provided
            if youtube_url:
                save_evaluation_to_supabase(youtube_url, child_age, results)
            
            # Return results
            return jsonify(results), 200
            
        finally:
            # Clean up temporary directory (only if we created one)
            if not use_existing and temp_dir and temp_dir.exists():
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