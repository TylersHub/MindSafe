"""
LLM Client for semantic content analysis.
Handles all interactions with language models for classification and labeling tasks.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Detect OpenAI version
try:
    from openai import OpenAI
    OPENAI_V1 = True
except ImportError:
    OPENAI_V1 = False


class LLMClient:
    """Wrapper for OpenAI API calls with specialized methods for content analysis."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", temperature: float = 0.1):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (if None, will use OPENAI_API_KEY env var)
            model: Model name to use (default: gpt-3.5-turbo for compatibility)
            temperature: Temperature for generation (lower = more deterministic)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        if OPENAI_V1:
            self.client = OpenAI(api_key=self.api_key)
        else:
            openai.api_key = self.api_key
            self.client = None
        
        self.model = model
        self.temperature = temperature
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Basic chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call
            
        Returns:
            The assistant's response text
        """
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **kwargs
        }
        
        try:
            if OPENAI_V1:
                # New API (openai >= 1.0.0)
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content
            else:
                # Old API (openai < 1.0.0)
                response = openai.ChatCompletion.create(**params)
                return response.choices[0].message.content
        except Exception as e:
            print(f"Error in LLM chat: {e}")
            raise
    
    def json_chat(self, system_prompt: str, user_prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Chat completion that enforces JSON response.
        
        Args:
            system_prompt: System message for the model
            user_prompt: User message/query
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response as a dictionary
        """
        # Add instruction to return JSON in the system prompt
        system_prompt = system_prompt + "\nYou MUST return ONLY valid JSON with no additional text or markdown."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_text = self.chat(messages, **kwargs)
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {response_text}")
            print(f"Error: {e}")
            # Return empty structure on failure
            return {}
    
    def classify_segment_events(self, text_segment: str, segment_duration: float = 30.0) -> Dict[str, Any]:
        """
        Classify semantic events in a text segment.
        
        Args:
            text_segment: The text to analyze
            segment_duration: Duration of the segment in seconds
            
        Returns:
            Dictionary with classified events and features:
            - prosocial_events: List of prosocial behaviors/events
            - aggressive_events: List of aggressive/violent events
            - fantasy_level: "none", "low", "medium", or "high"
            - sel_strategies: List of social-emotional learning strategies shown
            - direct_address: Whether speaker addresses viewer directly
            - fear_intense: Whether content is scary/intense for children
            - impossible_events: List of reality-violating events
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
        
        # Ensure all expected keys exist
        default_result = {
            "prosocial_events": [],
            "aggressive_events": [],
            "fantasy_level": "none",
            "sel_strategies": [],
            "direct_address": False,
            "fear_intense": False,
            "impossible_events": []
        }
        default_result.update(result)
        
        return default_result
    
    def rate_narrative_coherence(self, segment_summaries: List[str]) -> Dict[str, float]:
        """
        Rate narrative coherence across segments using LLM.
        
        Args:
            segment_summaries: List of short summaries of consecutive segments
            
        Returns:
            Dictionary with:
            - adjacent_similarity_mean: Average coherence between adjacent segments (0-1)
            - topic_jumps: Fraction of segments with abrupt topic changes (0-1)
        """
        if not segment_summaries or len(segment_summaries) < 2:
            return {"adjacent_similarity_mean": 1.0, "topic_jumps": 0.0}
        
        system_prompt = """You are analyzing narrative coherence in children's media.
Given a sequence of segment summaries, evaluate how well the story flows.
Return ONLY valid JSON with no additional text."""

        summaries_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(segment_summaries)])
        
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
            "adjacent_similarity_mean": result.get("adjacent_similarity_mean", 0.5),
            "topic_jumps": result.get("topic_jumps", 0.3)
        }
    
    def generate_segment_summary(self, text_segment: str) -> str:
        """
        Generate a short summary of a text segment.
        
        Args:
            text_segment: The text to summarize
            
        Returns:
            A one-sentence summary
        """
        system_prompt = "You are summarizing children's media content. Create brief, one-sentence summaries."
        
        user_prompt = f"""Summarize this segment in ONE simple sentence (suitable for a children's show):

{text_segment}

Summary:"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat(messages, max_tokens=100).strip()
    
    def estimate_language_metrics_llm(self, transcript: str) -> Dict[str, float]:
        """
        Optional: Use LLM to estimate language complexity metrics.
        This is an alternative to spaCy-based analysis.
        
        Args:
            transcript: Full transcript text
            
        Returns:
            Dictionary with language metrics
        """
        system_prompt = """You are analyzing language complexity in children's media.
Evaluate the transcript and return language metrics as JSON."""

        user_prompt = f"""Analyze this transcript for language complexity:

{transcript[:2000]}  # Truncate if too long

Return JSON with these metrics:
{{
  "vocabulary_richness": 0.0 to 1.0 (variety of unique words),
  "sentence_complexity": 0.0 to 1.0 (average sentence length/complexity),
  "advanced_vocabulary_fraction": 0.0 to 1.0 (fraction of words above basic tier),
  "question_frequency": 0.0 to 1.0 (relative frequency of questions)
}}"""

        return self.json_chat(system_prompt, user_prompt)

