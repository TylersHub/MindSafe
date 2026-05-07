"""
Master orchestrator script for evaluating video content.
Coordinates all analysis modules and generates comprehensive evaluation reports.
"""

import os
import sys
import json
import argparse
from typing import Dict, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import all components
from .video_preprocess import (
    extract_audio, detect_shots, transcribe_audio,
    get_video_duration, load_existing_transcript
)
from .metrics_pacing_audio import compute_pacing_audio_features
from .metrics_text_basic import compute_basic_text_metrics
from .metrics_llm_semantic import (
    llm_label_segments, compute_event_metrics_from_labels,
    compute_narrative_metrics
)
from .scoring import (
    assign_age_band, compute_dimension_scores,
    aggregate_dev_score, aggregate_brainrot_index,
    generate_recommendations, interpret_scores
)
from .llm_client import LLMClient
from .config import AGE_BANDS, LLM_CONFIG


def evaluate_video(video_path: str, 
                   child_age: float,
                   llm_client: Optional[LLMClient] = None,
                   outputs_dir: Optional[str] = None,
                   use_existing_transcript: bool = True,
                   compute_motion: bool = False) -> Dict[str, Any]:
    """
    Evaluate a video for developmental appropriateness.
    
    Args:
        video_path: Path to video file
        child_age: Age of child in years
        llm_client: LLMClient instance (if None, will create one)
        outputs_dir: Directory containing pre-extracted outputs (transcript, audio, etc.)
        use_existing_transcript: Whether to use existing transcript if available
        compute_motion: Whether to compute motion metrics (slow)
        
    Returns:
        Dictionary with complete evaluation results
    """
    print(f"\n{'='*60}")
    print(f"Evaluating video: {os.path.basename(video_path)}")
    print(f"Child age: {child_age} years")
    print(f"{'='*60}\n")
    
    # Initialize LLM client if not provided
    if llm_client is None:
        print("Initializing LLM client...")
        llm_client = LLMClient(
            model=LLM_CONFIG["model"],
            temperature=LLM_CONFIG["temperature"]
        )
    
    # Step 1: Preprocess video
    print("Step 1: Preprocessing video...")
    
    # Check if outputs directory has existing files
    audio_path = None
    transcript_segments = None
    
    if outputs_dir and os.path.exists(outputs_dir):
        print(f"  Checking for existing outputs in {outputs_dir}...")
        
        # Look for transcript
        transcript_candidates = [
            os.path.join(outputs_dir, "speech_transcript.txt"),
            os.path.join(outputs_dir, "transcript.txt"),
            os.path.join(outputs_dir, "video_llm_transcript.txt"),
        ]
        
        for transcript_path in transcript_candidates:
            if os.path.exists(transcript_path):
                print(f"  Found existing transcript: {transcript_path}")
                transcript_segments = load_existing_transcript(transcript_path)
                break
        
        # Look for audio
        audio_candidates = [
            os.path.join(outputs_dir, "audio_only.m4a"),
            os.path.join(outputs_dir, "audio_only.wav"),
            os.path.join(outputs_dir, "audio.wav"),
        ]
        
        for audio_candidate in audio_candidates:
            if os.path.exists(audio_candidate):
                print(f"  Found existing audio: {audio_candidate}")
                audio_path = audio_candidate
                break
    
    # Extract audio if not found
    if audio_path is None:
        print("  Extracting audio...")
        audio_path = extract_audio(video_path)
    
    # Detect shots
    print("  Detecting shots...")
    shots = detect_shots(video_path)
    print(f"  Found {len(shots)} shots")
    
    # Transcribe if not already done
    if transcript_segments is None:
        print("  Transcribing audio...")
        transcript_segments = transcribe_audio(audio_path, use_api=True)
        print(f"  Transcribed {len(transcript_segments)} segments")
    else:
        print(f"  Using existing transcript with {len(transcript_segments)} segments")
    
    # Get duration
    duration_sec = get_video_duration(video_path)
    if transcript_segments and len(transcript_segments) > 0:
        transcript_duration = max([seg.end for seg in transcript_segments])
        if transcript_duration > duration_sec:
            duration_sec = transcript_duration
    
    duration_min = duration_sec / 60.0
    print(f"  Video duration: {duration_sec:.1f}s ({duration_min:.1f} minutes)")
    
    # Step 2: Compute pacing and audio metrics
    print("\nStep 2: Computing pacing and audio metrics...")
    pacing_audio = compute_pacing_audio_features(video_path, audio_path, shots)
    print(f"  Cuts per minute: {pacing_audio.get('cuts_per_minute', 0):.1f}")
    print(f"  Average shot length: {pacing_audio.get('avg_shot_length', 0):.1f}s")
    print(f"  Loudness: {pacing_audio.get('loudness_mean', 0):.1f} dB")
    
    # Step 3: Compute basic text metrics
    print("\nStep 3: Computing text metrics...")
    text_basic = compute_basic_text_metrics(transcript_segments)
    print(f"  Type-token ratio: {text_basic.get('type_token_ratio', 0):.2f}")
    print(f"  Mean utterance length: {text_basic.get('mean_utterance_length', 0):.1f} words")
    print(f"  Question rate: {text_basic.get('question_rate', 0):.1f} per minute")
    
    # Step 4: Semantic metrics
    print("\nStep 4: Computing semantic metrics...")
    # If an LLM client is available, use it; otherwise fall back to fast heuristics
    if llm_client is not None:
        print("  Using LLM-based semantic labeling...")
        segment_labels = llm_label_segments(
            transcript_segments,
            llm_client,
            chunk_duration=LLM_CONFIG["segment_duration"],
        )
        print(f"  Labeled {len(segment_labels)} segments")
        semantic_metrics = compute_event_metrics_from_labels(
            segment_labels, duration_min
        )
    else:
        print("  Using heuristic semantic metrics (no LLM)...")
        semantic_metrics = compute_event_metrics_heuristic(
            transcript_segments, duration_min
        )
    print(f"  Prosocial rate: {semantic_metrics['prosocial_rate']:.1f} per minute")
    print(f"  Aggression rate: {semantic_metrics['aggression_rate']:.1f} per minute")
    print(f"  Prosocial ratio: {semantic_metrics['prosocial_ratio']:.2f}")
    
    # Step 5: Narrative coherence
    print("\nStep 5: Computing narrative coherence...")
    # Prefer fast, local embedding-based coherence; fall back to defaults on error
    narrative_metrics = compute_narrative_metrics(
        transcript_segments,
        llm_client=llm_client if llm_client is not None else None,
        use_embeddings=True,
        chunk_duration=LLM_CONFIG["segment_duration"],
    )
    print(
        f"  Adjacent similarity: {narrative_metrics.get('adjacent_similarity_mean', 0):.2f}"
    )
    print(f"  Topic jumps: {narrative_metrics.get('topic_jumps', 0):.2f}")
    
    # Step 6: Merge all raw metrics
    print("\nStep 6: Merging metrics...")
    raw_metrics = {
        **pacing_audio,
        **text_basic,
        **semantic_metrics,
        **narrative_metrics,
        "duration_minutes": duration_min,
        "duration_seconds": duration_sec
    }
    
    # Step 7: Scoring
    print("\nStep 7: Computing scores...")
    age_band = assign_age_band(child_age)
    age_band_label = AGE_BANDS[age_band]["label"]
    print(f"  Age band: {age_band} ({age_band_label})")
    
    dimension_scores = compute_dimension_scores(raw_metrics, age_band)
    print(f"  Dimension scores:")
    for dim, score in dimension_scores.items():
        print(f"    {dim}: {score:.1f}/100")
    
    dev_score = aggregate_dev_score(dimension_scores, age_band)
    brainrot_ix = aggregate_brainrot_index(dimension_scores, age_band)
    
    print(f"\n  DEVELOPMENTAL SCORE: {dev_score:.1f}/100")
    print(f"  BRAINROT INDEX: {brainrot_ix:.1f}/100")
    
    # Step 8: Generate recommendations
    print("\nStep 8: Generating recommendations...")
    recommendations = generate_recommendations(dimension_scores, raw_metrics, age_band)
    interpretations = interpret_scores(dev_score, brainrot_ix)
    
    # Compile final results
    results = {
        "metadata": {
            "video_path": video_path,
            "video_name": os.path.basename(video_path),
            "evaluation_timestamp": datetime.now().isoformat(),
            "child_age": child_age,
            "age_band": age_band,
            "age_band_label": age_band_label,
            "duration_seconds": duration_sec,
            "duration_minutes": duration_min
        },
        "raw_metrics": raw_metrics,
        "dimension_scores": dimension_scores,
        "overall_scores": {
            "development_score": dev_score,
            "brainrot_index": brainrot_ix
        },
        "interpretations": interpretations,
        "recommendations": recommendations
    }
    
    print(f"\n{'='*60}")
    print("Evaluation complete!")
    print(f"{'='*60}\n")
    
    return results


def save_results(results: Dict[str, Any], output_path: str):
    """Save evaluation results to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {output_path}")


def print_summary(results: Dict[str, Any]):
    """Print a human-readable summary of results."""
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    
    metadata = results["metadata"]
    print(f"\nVideo: {metadata['video_name']}")
    print(f"Age: {metadata['child_age']} years ({metadata['age_band_label']})")
    print(f"Duration: {metadata['duration_minutes']:.1f} minutes")
    
    scores = results["overall_scores"]
    interp = results["interpretations"]
    
    print(f"\n{'SCORES':^60}")
    print("-"*60)
    print(f"  Developmental Score: {scores['development_score']:.1f}/100")
    print(f"    → {interp['developmental']}")
    print(f"\n  Brainrot Index: {scores['brainrot_index']:.1f}/100")
    print(f"    → {interp['brainrot']}")
    print(f"\n  Overall: {interp['overall']}")
    
    recs = results["recommendations"]
    
    if recs["strengths"]:
        print(f"\n{'STRENGTHS':^60}")
        print("-"*60)
        for strength in recs["strengths"]:
            print(f"  ✓ {strength}")
    
    if recs["concerns"]:
        print(f"\n{'CONCERNS':^60}")
        print("-"*60)
        for concern in recs["concerns"]:
            print(f"  ⚠ {concern}")
    
    print("\n" + "="*60 + "\n")


def main():
    """Command-line interface for video evaluation."""
    parser = argparse.ArgumentParser(
        description="Evaluate children's video content for developmental appropriateness"
    )
    parser.add_argument(
        "video_path",
        help="Path to video file"
    )
    parser.add_argument(
        "--age",
        type=float,
        required=True,
        help="Child's age in years"
    )
    parser.add_argument(
        "--outputs-dir",
        help="Directory containing pre-extracted outputs (transcript, audio, etc.)"
    )
    parser.add_argument(
        "--output",
        help="Path to save JSON results (default: evaluation_results.json)"
    )
    parser.add_argument(
        "--no-motion",
        action="store_true",
        help="Skip motion computation (faster)"
    )
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        sys.exit(1)
    
    if args.age < 0 or args.age > 10:
        print(f"Warning: Age {args.age} is outside typical range (0-8 years)")
    
    # Initialize LLM client
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required. Set OPENROUTER_API_KEY env var or use --api-key")
        sys.exit(1)
    
    llm_client = LLMClient(api_key=api_key)
    
    # Run evaluation
    try:
        results = evaluate_video(
            video_path=args.video_path,
            child_age=args.age,
            llm_client=llm_client,
            outputs_dir=args.outputs_dir,
            compute_motion=not args.no_motion
        )
        
        # Print summary
        print_summary(results)
        
        # Save results
        output_path = args.output or "evaluation_results.json"
        save_results(results, output_path)
        
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

