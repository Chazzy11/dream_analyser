import re
import numpy as np
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Dict, Tuple
from .models import DreamAnalysis


class Dreamanalyser:
    """Analyses dreams for emotional and dynamic content."""
    
    def __init__(self):
        # Predefined word lists for dream analysis
        self.upper_words = {
            'flying', 'soaring', 'light', 'bright', 'laughing', 'happy', 'joy', 'love',
            'celebration', 'success', 'winning', 'beautiful', 'wonderful', 'amazing',
            'peaceful', 'calm', 'serene', 'blissful', 'euphoric', 'radiant', 'golden'
        }
        
        self.downer_words = {
            'falling', 'dark', 'scary', 'fear', 'nightmare', 'death', 'crying', 'sad',
            'angry', 'lost', 'trapped', 'drowning', 'monster', 'shadow', 'blood',
            'pain', 'hurt', 'broken', 'empty', 'alone', 'hopeless', 'terrified'
        }
        
        self.dynamic_words = {
            'running', 'chasing', 'moving', 'racing', 'jumping', 'dancing', 'fighting',
            'flying', 'swimming', 'climbing', 'rushing', 'spinning', 'whirling',
            'exploding', 'crashing', 'thundering', 'storming', 'vibrating', 'shaking'
        }
        
        self.static_words = {
            'sitting', 'standing', 'waiting', 'watching', 'staring', 'frozen', 'still',
            'motionless', 'calm', 'peaceful', 'quiet', 'silent', 'empty', 'void',
            'meditation', 'sleeping', 'resting', 'contemplating', 'observing'
        }

    def analyze_dream(self, dream_text: str) -> DreamAnalysis:
        """Analyze a dream text and return emotional/dynamic scores."""
        # Clean and process text
        cleaned_text = self._clean_text(dream_text)
        
        # Get sentiment analysis
        blob = TextBlob(cleaned_text)
        sentiment_polarity = blob.sentiment.polarity
        
        # Calculate scores
        upper_downer = self._calculate_emotional_score(cleaned_text, sentiment_polarity)
        static_dynamic = self._calculate_dynamic_score(cleaned_text)
        
        # Extract keywords
        keywords = self._extract_keywords(cleaned_text)
        
        # Calculate confidence based on text length and keyword matches
        confidence = self._calculate_confidence(cleaned_text, keywords)
        
        return DreamAnalysis(
            upper_downer_score=upper_downer,
            static_dynamic_score=static_dynamic,
            confidence=confidence,
            keywords=keywords
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        return text
    
    def _calculate_emotional_score(self, text: str, sentiment: float) -> float:
        """Calculate upper/downer score (-1 to 1)."""
        words = set(text.split())
        
        upper_count = len(words & self.upper_words)
        downer_count = len(words & self.downer_words)
        
        # Combine keyword-based scoring with sentiment analysis
        keyword_score = 0
        if upper_count > 0 or downer_count > 0:
            keyword_score = (upper_count - downer_count) / (upper_count + downer_count)
        
        # Weight sentiment analysis and keyword matching
        final_score = 0.6 * sentiment + 0.4 * keyword_score
        
        # Ensure score is within bounds
        return max(-1.0, min(1.0, final_score))
    
    def _calculate_dynamic_score(self, text: str) -> float:
        """Calculate static/dynamic score (-1 to 1)."""
        words = set(text.split())
        
        dynamic_count = len(words & self.dynamic_words)
        static_count = len(words & self.static_words)
        
        if dynamic_count == 0 and static_count == 0:
            # Default to slightly dynamic for most dreams
            return 0.1
        
        total = dynamic_count + static_count
        if total == 0:
            return 0.0
        
        score = (dynamic_count - static_count) / total
        return max(-1.0, min(1.0, score))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from dream text."""
        words = text.split()
        
        # Find matches with our predefined word sets
        all_keywords = self.upper_words | self.downer_words | self.dynamic_words | self.static_words
        found_keywords = [word for word in words if word in all_keywords]
        
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for keyword in found_keywords:
            if keyword not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword)
        
        return unique_keywords[:10]  # Limit to top 10 keywords
    
    def _calculate_confidence(self, text: str, keywords: List[str]) -> float:
        """Calculate confidence in the analysis."""
        text_length = len(text.split())
        keyword_count = len(keywords)
        
        # Base confidence on text length (more text = higher confidence)
        length_factor = min(1.0, text_length / 50.0)  # Cap at 50 words
        
        # Boost confidence based on keyword matches
        keyword_factor = min(1.0, keyword_count / 5.0)  # Cap at 5 keywords
        
        confidence = 0.5 + 0.3 * length_factor + 0.2 * keyword_factor
        return min(1.0, confidence)