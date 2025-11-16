"""
AI-powered analysis using OpenAI models.
Includes dialogue extraction, segment transcription, and scene analysis.
"""

from pathlib import Path
from typing import List

try:
    from .config import client, VISION_MODEL, OPENAI_V1
    from .utils import safe_responses_create
except ImportError:
    from config import client, VISION_MODEL, OPENAI_V1
    from utils import safe_responses_create


def extract_dialogue_for_timerange(
    full_transcript: str,
    start_time: float,
    end_time: float,
    total_duration: float
) -> str:
    """
    Extract approximate dialogue for a specific time range.
    Uses proportional text extraction based on time ratios.
    """
    if not full_transcript or total_duration <= 0:
        return "[No dialogue available]"
    
    # Calculate proportional position in the transcript
    start_ratio = start_time / total_duration
    end_ratio = end_time / total_duration
    
    # Extract the corresponding portion of text
    transcript_length = len(full_transcript)
    start_pos = int(start_ratio * transcript_length)
    end_pos = int(end_ratio * transcript_length)
    
    segment_dialogue = full_transcript[start_pos:end_pos].strip()
    
    if not segment_dialogue:
        return "[No dialogue in this segment]"
    
    return segment_dialogue


def generate_segment_transcript(
    frame_paths: List[Path],
    segment_num: int,
    total_segments: int,
    start_time: float,
    end_time: float,
    full_speech_transcript: str,
    total_duration: float,
) -> str:
    """
    Generate transcript for a single video segment with relevant dialogue.
    """
    # Extract dialogue specific to this time segment
    segment_dialogue = extract_dialogue_for_timerange(
        full_speech_transcript,
        start_time,
        end_time,
        total_duration
    )
    
    if not frame_paths:
        return (
            f"[SEGMENT {segment_num}/{total_segments}: {start_time:.1f}s - {end_time:.1f}s]\n"
            f"(No frames available)\n\n"
            f"DIALOGUE IN THIS SEGMENT:\n\"{segment_dialogue}\"\n"
        )

    print(f"  Processing segment {segment_num}/{total_segments} ({start_time:.1f}s - {end_time:.1f}s)...")
    
    if not OPENAI_V1:
        # Old API doesn't support vision file uploads
        return (
            f"[SEGMENT {segment_num}/{total_segments}: {start_time:.1f}s - {end_time:.1f}s]\n"
            f"(Vision analysis requires openai>=1.0.0. Please upgrade: pip install --upgrade openai)\n\n"
            f"DIALOGUE IN THIS SEGMENT:\n\"{segment_dialogue}\"\n"
        )
    
    print(f"  Uploading {len(frame_paths)} frames...")

    file_ids = []
    for frame in frame_paths:
        try:
            with open(frame, "rb") as img_file:
                uploaded = client.files.create(
                    file=img_file,
                    purpose="vision",
                )
                file_ids.append(uploaded.id)
        except Exception as e:
            print(f"[ERROR] Uploading frame {frame} failed: {e}")

    if not file_ids:
        return (
            f"[SEGMENT {segment_num}/{total_segments}: {start_time:.1f}s - {end_time:.1f}s]\n"
            f"(No visual frames could be processed)\n\n"
            f"DIALOGUE IN THIS SEGMENT:\n\"{segment_dialogue}\"\n"
        )

    content = [
        {
            "type": "input_text",
            "text": (
                f"You are analyzing SEGMENT {segment_num} of {total_segments} from a video.\n"
                f"Time range: {start_time:.1f}s to {end_time:.1f}s (duration: {end_time - start_time:.1f}s)\n\n"
                "Create a detailed transcript for THIS SEGMENT that includes:\n\n"
                "1. SETTING & SCENE:\n"
                "   • Location and environment\n"
                "   • Atmosphere and lighting\n"
                "   • Important props or objects\n\n"
                "2. ACTIONS & EVENTS:\n"
                "   • What happens in this segment\n"
                "   • Character movements and actions\n"
                "   • Interactions and reactions\n"
                "   • Important visual moments\n\n"
                "3. DIALOGUE (MUST INTEGRATE):\n"
                "   • The dialogue below was spoken during THIS SPECIFIC segment\n"
                "   • Match each line to the appropriate visual moment\n"
                "   • Identify who is speaking based on visual cues\n"
                "   • Note emotional tone and delivery\n"
                "   • Format as: CHARACTER: \"dialogue\"\n\n"
                "4. CONTINUITY:\n"
                "   • Note transitions from previous segment\n"
                "   • Set up continuation to next segment\n\n"
                "FORMAT:\n"
                "• Start with [SCENE: Description] if location changes\n"
                "• Integrate dialogue naturally into the narrative\n"
                "• Write 2–3 detailed paragraphs\n"
                "• Be specific and vivid\n\n"
                "=" * 70 + "\n"
                "DIALOGUE SPOKEN IN THIS TIME SEGMENT:\n"
                "=" * 70 + "\n"
                f"\"{segment_dialogue}\"\n"
                "=" * 70 + "\n\n"
                f"Now analyze these {len(frame_paths)} frames and create a detailed description "
                f"that integrates the dialogue above with what's happening visually:"
            ),
        }
    ]

    for i, file_id in enumerate(file_ids, 1):
        content.append({
            "type": "input_text",
            "text": f"\n--- Frame {i}/{len(file_ids)} ---\n"
        })
        content.append({
            "type": "input_image",
            "file_id": file_id,
        })

    text = safe_responses_create(
        client,
        model=VISION_MODEL,
        input=[{"role": "user", "content": content}],
    )

    if text is None:
        return (
            f"[SEGMENT {segment_num}/{total_segments}: {start_time:.1f}s - {end_time:.1f}s]\n"
            f"(Vision API failed)\n\n"
            f"DIALOGUE IN THIS SEGMENT:\n\"{segment_dialogue}\"\n"
        )

    return text


def generate_dialogue_transcript(speech_transcript: str) -> str:
    """
    Turn raw ASR text into a dialogue-style transcript with speaker labels.
    """
    if not speech_transcript:
        return "[DIALOGUE TRANSCRIPT UNAVAILABLE – empty transcription]"

    if speech_transcript.startswith("[TRANSCRIPTION FAILED]"):
        return (
            "DIALOGUE TRANSCRIPT\n"
            "===================\n"
            "Speaker diarization unavailable because transcription failed.\n\n"
            "Raw content:\n"
            f"{speech_transcript}\n"
        )

    prompt = (
        "You are given a raw automatic speech recognition transcript of a video.\n"
        "Your job is to turn it into a clean DIALOGUE transcript that labels who speaks.\n\n"
        "REQUIREMENTS:\n"
        "1. Do NOT summarize or omit content. Keep ALL lines and information.\n"
        "2. Split the text into natural utterances.\n"
        "3. Assign speaker labels like SPEAKER 1, SPEAKER 2, NARRATOR, CHILD 1, etc.\n"
        "   - Be consistent: the same person must always keep the same label.\n"
        "   - Infer speaker changes from the text structure and cues.\n"
        "4. If you are unsure who is speaking, still assign a consistent label.\n"
        "5. Keep the original chronological order of everything said.\n"
        "6. Use this format:\n"
        "   SPEAKER 1: \"...\"\n"
        "   SPEAKER 2: \"...\"\n"
        "   NARRATOR: \"...\"\n\n"
        "7. DO NOT drop jokes, asides, or filler words; preserve the full content.\n\n"
        "Now convert this raw transcript into a fully labeled dialogue transcript:\n\n"
    )

    text = safe_responses_create(
        client,
        model=VISION_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt + speech_transcript}
                ],
            }
        ],
    )

    if text is None:
        return (
            "DIALOGUE TRANSCRIPT (FALLBACK)\n"
            "===============================\n"
            "Speaker diarization failed. Below is the raw transcript:\n\n"
            f"{speech_transcript}\n"
        )

    return text


def generate_scene_summary(vllm_transcript: str) -> str:
    """
    Take the long, detailed multimodal analysis and turn it into:
      - scene-by-scene breakdown (in order, covering entire video)
      - plus a final 'Global Evaluation' section.
    """
    if not vllm_transcript:
        return "[SCENE SUMMARY UNAVAILABLE – no analysis text]"

    prompt = (
        "You are given a detailed, segment-by-segment analysis of a video "
        "that already includes both visual descriptions and dialogue.\n\n"
        "YOUR JOB:\n"
        "1. Infer the SCENE structure of the video (changes in location, time, or activity).\n"
        "2. Produce a scene-by-scene breakdown that covers the ENTIRE video in order.\n"
        "3. Include ALL important events mentioned in the analysis; do NOT skip segments.\n"
        "4. For each scene, include:\n"
        "   - SCENE number\n"
        "   - Approximate time range (if possible, based on the text; otherwise, 'approx.')\n"
        "   - Brief title (one line)\n"
        "   - 1–3 paragraphs describing exactly what happens: actions, dialogue, emotions.\n"
        "5. At the end, add a 'GLOBAL EVALUATION' section that:\n"
        "   - Summarizes the overall story\n"
        "   - Comments on pacing, tone, and structure\n"
        "   - Notes any recurring themes or patterns\n"
        "   - Evaluates the video as a complete unit.\n\n"
        "FORMATTING:\n"
        "Use this structure exactly:\n\n"
        "SCENE 1 [00:00–00:35] – Short scene title\n"
        "Detailed description...\n\n"
        "SCENE 2 [00:35–01:10] – Short scene title\n"
        "Detailed description...\n\n"
        "...\n\n"
        "GLOBAL EVALUATION\n"
        "-----------------\n"
        "Your global comments here.\n\n"
        "Now, here is the full analysis to rewrite into that format:\n\n"
    )

    text = safe_responses_create(
        client,
        model=VISION_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt + vllm_transcript}
                ],
            }
        ],
    )

    if text is None:
        return (
            "SCENE SUMMARY (FALLBACK)\n"
            "========================\n"
            "Scene segmentation failed. Below is the original full analysis:\n\n"
            f"{vllm_transcript}\n"
        )

    return text

