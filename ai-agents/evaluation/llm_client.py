"""
LLM Client for semantic content analysis using OpenRouter.

Usage:
    from llm_client import LLMClient

    client = LLMClient()
    text = client.chat([{"role": "user", "content": "Say hi in one sentence"}])
    print(text)

Env vars:
    OPENROUTER_API_KEY   (required)
    OPENROUTER_BASE_URL  (optional, default: https://openrouter.ai/api/v1)
    OPENROUTER_MODEL     (optional, default: google/gemini-2.0-flash-lite)
"""

import json
import os
from typing import Dict, List, Optional, Any

import httpx
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


class LLMClient:
    """
    Wrapper for OpenRouter /chat/completions API with helpers
    for content analysis and JSON responses.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: OpenRouter API key (if None, uses OPENROUTER_API_KEY)
            model: Model name (if None, uses OPENROUTER_MODEL or default Gemini)
            temperature: Sampling temperature (lower = more deterministic)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key must be provided via OPENROUTER_API_KEY env var."
            )

        # IMPORTANT: base_url MUST NOT include /chat/completions
        self.base_url = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).rstrip("/")

        # Default Gemini-ish model via OpenRouter, override via env or arg
        self.model = (
            model
            or os.getenv("OPENROUTER_MODEL")
            or "google/gemini-2.0-flash-lite"
        )
        self.temperature = temperature

        # Shared HTTP client
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                # Optional etiquette headers for OpenRouter:
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://mindsafe.local"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "MindSafe Children Video Evaluator"),
            },
            timeout=60.0,
        )

    def _post_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Low-level helper to call OpenRouter's chat completions endpoint.

        On success: returns parsed JSON.
        On HTTP error: logs and tries to return server JSON (containing "error" if present).
        On other errors: logs and returns {}.
        """
        try:
            resp = self._http.post("/chat/completions", json=payload)

            # Try to parse JSON first so we can inspect any error payload
            try:
                data = resp.json()
            except Exception:
                data = {}

            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                print(f"[LLMClient] HTTP error from OpenRouter chat API: {e}")
                try:
                    print("[LLMClient] Response body:", e.response.text[:1000])
                except Exception:
                    pass
                # Prefer returning whatever JSON the server sent (likely contains "error")
                try:
                    return e.response.json()
                except Exception:
                    return data or {}

            return data
        except httpx.HTTPError as e:
            print(f"[LLMClient] Network error calling OpenRouter chat API: {e}")
            return {}
        except Exception as e:
            print(f"[LLMClient] Unexpected error calling OpenRouter chat API: {e}")
            return {}

    # ---------- Basic Chat ----------

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Basic chat completion.

        Args:
            messages: List of dicts with 'role' and 'content'
            **kwargs: Extra params for the API (e.g., max_tokens)

        Returns:
            The assistant's response text or a safe fallback string.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        payload.update(kwargs)

        data = self._post_chat(payload)

        if not data:
            print("[LLMClient] Empty response from OpenRouter.")
            return "[LLM ERROR] Empty response from upstream."

        # Handle explicit error objects from OpenRouter
        if "error" in data:
            print(f"[LLMClient] OpenRouter error: {data['error']}")
            return "[LLM ERROR] Upstream model error."

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            print(f"[LLMClient] Unexpected response format from OpenRouter: {e}")
            print(f"[LLMClient] Raw response: {json.dumps(data, indent=2)[:2000]}")
            return "[LLM ERROR] Unable to generate response."

    # ---------- JSON Chat Helper ----------

    def json_chat(self, system_prompt: str, user_prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Chat completion that enforces JSON response.

        Args:
            system_prompt: System message
            user_prompt: User message
            **kwargs: Extra params

        Returns:
            Parsed JSON dict ({} on failure).
        """
        system_prompt = (
            system_prompt
            + "\nYou MUST return ONLY valid JSON with no additional text or markdown."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        payload.update(kwargs)

        data = self._post_chat(payload)

        if not data:
            print("[LLMClient] Empty response from OpenRouter in json_chat.")
            return {}

        if "error" in data:
            print(f"[LLMClient] OpenRouter error in json_chat: {data['error']}")
            return {}

        try:
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            print(f"[LLMClient] Failed to parse JSON response: {e}")
            print(f"[LLMClient] Raw response: {json.dumps(data, indent=2)[:2000]}")
            return {}

    # ---------- Specialized Helpers ----------

    def classify_segment_events(
        self, text_segment: str, segment_duration: float = 30.0
    ) -> Dict[str, Any]:
        """
        Classify semantic events in a text segment.

        Returns:
            {
              "prosocial_events": [...],
              "aggressive_events": [...],
              "fantasy_level": "none"/"low"/"medium"/"high",
              "sel_strategies": [...],
              "direct_address": bool,
              "fear_intense": bool,
              "impossible_events": [...]
            }
        """
        system_prompt = """You are a child development expert analyzing children's media content.
Your task is to label content for developmental appropriateness and educational value.
You must return ONLY valid JSON with no additional text.

Analyze the provided transcript segment and identify:
1. Prosocial events: sharing, helping, cooperating, empathy, kindness, apologizing, etc.
2. Aggressive events: hitting, yelling, meanness, conflicts, violence (even if cartoon/mild)
3. Fantasy level: How fantastical/imaginative is the content?
4. SEL strategies: Explicit social-emotional learning like "take deep breaths", "use your words", emotion labeling
5. Direct address: Does a character speak directly to the viewer (e.g., "Can you help me?", "Let's count together!")
6. Fear/intensity: Is this segment scary, intense, or overwhelming for young children?
7. Impossible events: Things that violate reality/physics in confusing ways for young kids

Be thorough but concise in your descriptions."""

        user_prompt = f"""Analyze this transcript segment from children's media:

TRANSCRIPT:
{text_segment}

Return JSON with this exact structure:
{{
  "prosocial_events": ["description1", "description2", ...],
  "aggressive_events": ["description1", "description2", ...],
  "fantasy_level": "none" or "low" or "medium" or "high",
  "sel_strategies": ["strategy1", "strategy2", ...],
  "direct_address": true or false,
  "fear_intense": true or false,
  "impossible_events": ["event1", "event2", ...]
}}

Only include events that actually occur in the transcript. Use empty lists if none found."""

        result = self.json_chat(system_prompt, user_prompt)

        default_result = {
            "prosocial_events": [],
            "aggressive_events": [],
            "fantasy_level": "none",
            "sel_strategies": [],
            "direct_address": False,
            "fear_intense": False,
            "impossible_events": [],
        }
        if isinstance(result, dict):
            default_result.update(result)

        return default_result

    def rate_narrative_coherence(self, segment_summaries: List[str]) -> Dict[str, float]:
        """
        Rate narrative coherence across segments using LLM.

        Returns:
            {
              "adjacent_similarity_mean": float,
              "topic_jumps": float
            }
        """
        if not segment_summaries or len(segment_summaries) < 2:
            return {"adjacent_similarity_mean": 1.0, "topic_jumps": 0.0}

        system_prompt = """You are analyzing narrative coherence in children's media.
Given a sequence of segment summaries, evaluate how well the story flows.
Return ONLY valid JSON with no additional text."""

        summaries_text = "\n".join(
            [f"{i+1}. {s}" for i, s in enumerate(segment_summaries)]
        )

        user_prompt = f"""Analyze the narrative coherence of these consecutive segments from a children's show:

SEGMENTS:
{summaries_text}

Evaluate:
1. adjacent_similarity_mean: Average coherence/connection between consecutive segments (0.0 = completely unrelated, 1.0 = perfectly connected)
2. topic_jumps: Fraction of transitions that are abrupt/jarring topic changes with no logical connection

Return JSON:
{{
  "adjacent_similarity_mean": 0.0 to 1.0,
  "topic_jumps": 0.0 to 1.0
}}"""

        result = self.json_chat(system_prompt, user_prompt)

        return {
            "adjacent_similarity_mean": float(result.get("adjacent_similarity_mean", 0.5)),
            "topic_jumps": float(result.get("topic_jumps", 0.3)),
        }

    def generate_segment_summary(self, text_segment: str) -> str:
        """
        Generate a short, one-sentence summary of a text segment.
        """
        system_prompt = (
            "You are summarizing children's media content. Create brief, one-sentence summaries."
        )

        user_prompt = f"""Summarize this segment in ONE simple sentence (suitable for a children's show):

{text_segment}

Summary:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.chat(messages, max_tokens=100).strip()

    def estimate_language_metrics_llm(self, transcript: str) -> Dict[str, float]:
        """
        Use LLM to estimate language complexity metrics.

        Returns something like:
            {
              "vocabulary_richness": float,
              "sentence_complexity": float,
              "advanced_vocabulary_fraction": float,
              "question_frequency": float
            }
        """
        system_prompt = """You are analyzing language complexity in children's media.
Evaluate the transcript and return language metrics as JSON."""

        # Truncate if huge
        truncated = transcript[:2000]

        user_prompt = f"""Analyze this transcript for language complexity:

{truncated}

Return JSON with these metrics:
{{
  "vocabulary_richness": 0.0 to 1.0 (variety of unique words),
  "sentence_complexity": 0.0 to 1.0 (average sentence length/complexity),
  "advanced_vocabulary_fraction": 0.0 to 1.0 (fraction of words above basic tier),
  "question_frequency": 0.0 to 1.0 (relative frequency of questions)
}}"""

        result = self.json_chat(system_prompt, user_prompt)

        return {
            "vocabulary_richness": float(result.get("vocabulary_richness", 0.5)),
            "sentence_complexity": float(result.get("sentence_complexity", 0.5)),
            "advanced_vocabulary_fraction": float(
                result.get("advanced_vocabulary_fraction", 0.3)
            ),
            "question_frequency": float(result.get("question_frequency", 0.3)),
        }


if __name__ == "__main__":
    """
    Tiny smoke test you can run with:
        python llm_client.py
    Make sure your OPENROUTER_API_KEY is set first.
    """
    try:
        client = LLMClient()
        msg = [{"role": "user", "content": "Say hi in one short friendly sentence."}]
        print("Chat test:", client.chat(msg))
    except Exception as e:
        print("Error running LLMClient smoke test:", e)
