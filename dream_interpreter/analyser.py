"""Dream analysis using either a Claude API call or a legacy rule-based fallback."""
import re
from typing import List

import anthropic
from textblob import TextBlob

from .models import DreamAnalysis

_TOOL_SCHEMA = [
    {
        "name": "record_dream_analysis",
        "description": "Record the structured analysis of a dream.",
        "input_schema": {
            "type": "object",
            "properties": {
                "upper_downer_score": {
                    "type": "number",
                    "minimum": -1,
                    "maximum": 1,
                    "description": (
                        "Emotional valence: -1 = deeply negative/fearful, "
                        "0 = neutral, 1 = joyful/transcendent."
                    ),
                },
                "static_dynamic_score": {
                    "type": "number",
                    "minimum": -1,
                    "maximum": 1,
                    "description": (
                        "Energy level: -1 = passive/still/observational, "
                        "0 = mixed, 1 = active/energetic/kinetic."
                    ),
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": (
                        "How clearly the text expresses emotional and energetic "
                        "content. Short or ambiguous texts score lower."
                    ),
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 10,
                    "description": "Up to 10 significant dream elements.",
                },
            },
            "required": [
                "upper_downer_score",
                "static_dynamic_score",
                "confidence",
                "keywords",
            ],
        },
    }
]

_SYSTEM_PROMPT = (
    "You are a dream analysis engine. Score the dream on two axes:\n"
    "- upper_downer_score: float in [-1, 1], where -1 is deeply negative/fearful, "
    "0 is neutral, 1 is joyful/transcendent.\n"
    "- static_dynamic_score: float in [-1, 1], where -1 is passive/still/observational, "
    "0 is mixed, 1 is active/energetic/kinetic.\n"
    "- confidence: float in [0, 1] reflecting how clearly the text expresses emotional "
    "and energetic content. Short or ambiguous texts score lower.\n"
    "- keywords: list of up to 10 significant dream elements (not limited to any "
    "predefined vocabulary).\n"
    "Use the provided tool to record your analysis."
)


class LLMDreamanalyser:  # pylint: disable=too-few-public-methods
    """Analyses dreams using the Claude API for context-aware scoring."""

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        anthropic_client: anthropic.AsyncAnthropic = None,
    ):
        """Initialise the analyser.

        Args:
            model: Claude model ID to use for analysis.
            anthropic_client: Optional pre-built Anthropic client (useful for testing).
        """
        self._client = anthropic_client or anthropic.AsyncAnthropic()
        self._model = model

    async def analyze_dream(self, dream_text: str) -> DreamAnalysis:
        """Analyse a dream via Claude API tool use and return structured scores.

        Args:
            dream_text: The raw dream description to analyse.

        Returns:
            A DreamAnalysis with scores and extracted keywords.
        """
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=256,
            temperature=0,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": dream_text}],
            tools=_TOOL_SCHEMA,
            tool_choice={"type": "any"},
        )
        tool_input = message.content[0].input
        return DreamAnalysis(**tool_input)


class LegacyDreamanalyser:  # pylint: disable=too-few-public-methods
    """Rule-based dream analyser using TextBlob sentiment and keyword matching."""

    def __init__(self):
        """Initialise predefined word sets for scoring."""
        self.upper_words = {
            "flying",
            "soaring",
            "light",
            "bright",
            "laughing",
            "happy",
            "joy",
            "love",
            "celebration",
            "success",
            "winning",
            "beautiful",
            "wonderful",
            "amazing",
            "peaceful",
            "calm",
            "serene",
            "blissful",
            "euphoric",
            "radiant",
            "golden",
        }

        self.downer_words = {
            "falling",
            "dark",
            "scary",
            "fear",
            "nightmare",
            "death",
            "crying",
            "sad",
            "angry",
            "lost",
            "trapped",
            "drowning",
            "monster",
            "shadow",
            "blood",
            "pain",
            "hurt",
            "broken",
            "empty",
            "alone",
            "hopeless",
            "terrified",
        }

        self.dynamic_words = {
            "running",
            "chasing",
            "moving",
            "racing",
            "jumping",
            "dancing",
            "fighting",
            "flying",
            "swimming",
            "climbing",
            "rushing",
            "spinning",
            "whirling",
            "exploding",
            "crashing",
            "thundering",
            "storming",
            "vibrating",
            "shaking",
        }

        self.static_words = {
            "sitting",
            "standing",
            "waiting",
            "watching",
            "staring",
            "frozen",
            "still",
            "motionless",
            "calm",
            "peaceful",
            "quiet",
            "silent",
            "empty",
            "void",
            "meditation",
            "sleeping",
            "resting",
            "contemplating",
            "observing",
        }

    def analyze_dream(self, dream_text: str) -> DreamAnalysis:
        """Analyse a dream text and return emotional/dynamic scores.

        Args:
            dream_text: The raw dream description to analyse.

        Returns:
            A DreamAnalysis with scores and extracted keywords.
        """
        cleaned_text = self._clean_text(dream_text)

        blob = TextBlob(cleaned_text)
        sentiment_polarity = blob.sentiment.polarity

        upper_downer = self._calculate_emotional_score(cleaned_text, sentiment_polarity)
        static_dynamic = self._calculate_dynamic_score(cleaned_text)
        keywords = self._extract_keywords(cleaned_text)
        confidence = self._calculate_confidence(cleaned_text, keywords)

        return DreamAnalysis(
            upper_downer_score=upper_downer,
            static_dynamic_score=static_dynamic,
            confidence=confidence,
            keywords=keywords,
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalise text."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = " ".join(text.split())
        return text

    def _calculate_emotional_score(self, text: str, sentiment: float) -> float:
        """Calculate upper/downer score (-1 to 1)."""
        words = set(text.split())

        upper_count = len(words & self.upper_words)
        downer_count = len(words & self.downer_words)

        keyword_score = 0
        if upper_count > 0 or downer_count > 0:
            keyword_score = (upper_count - downer_count) / (upper_count + downer_count)

        final_score = 0.6 * sentiment + 0.4 * keyword_score
        return max(-1.0, min(1.0, final_score))

    def _calculate_dynamic_score(self, text: str) -> float:
        """Calculate static/dynamic score (-1 to 1)."""
        words = set(text.split())

        dynamic_count = len(words & self.dynamic_words)
        static_count = len(words & self.static_words)

        if dynamic_count == 0 and static_count == 0:
            return 0.1

        total = dynamic_count + static_count
        if total == 0:
            return 0.0

        score = (dynamic_count - static_count) / total
        return max(-1.0, min(1.0, score))

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from dream text."""
        words = text.split()

        all_keywords = (
            self.upper_words
            | self.downer_words
            | self.dynamic_words
            | self.static_words
        )
        found_keywords = [word for word in words if word in all_keywords]

        unique_keywords = []
        seen = set()
        for keyword in found_keywords:
            if keyword not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword)

        return unique_keywords[:10]

    def _calculate_confidence(self, text: str, keywords: List[str]) -> float:
        """Calculate confidence in the analysis."""
        text_length = len(text.split())
        keyword_count = len(keywords)

        length_factor = min(1.0, text_length / 50.0)
        keyword_factor = min(1.0, keyword_count / 5.0)

        confidence = 0.5 + 0.3 * length_factor + 0.2 * keyword_factor
        return min(1.0, confidence)


# Backward-compatibility alias — existing imports of Dreamanalyser still work.
Dreamanalyser = LegacyDreamanalyser
