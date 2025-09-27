import pytest
from dream_interpreter.analyser import Dreamanalyser


class TestDreamanalyser:
    """Test cases for the Dreamanalyser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyser = Dreamanalyser()
    
    def test_positive_dream_analysis(self):
        """Test analysis of a positive dream."""
        dream_text = "I was flying through beautiful golden clouds, feeling happy and free"
        analysis = self.analyser.analyze_dream(dream_text)
        
        assert analysis.upper_downer_score > 0, "Should be positive (upper)"
        assert analysis.static_dynamic_score > 0, "Should be dynamic (flying)"
        assert analysis.confidence > 0.5, "Should have reasonable confidence"
        assert "flying" in analysis.keywords
        assert "happy" in analysis.keywords
    
    def test_negative_dream_analysis(self):
        """Test analysis of a negative dream."""
        dream_text = "I was trapped in a dark room, feeling scared and alone"
        analysis = self.analyser.analyze_dream(dream_text)
        
        assert analysis.upper_downer_score < 0, "Should be negative (downer)"
        assert analysis.confidence > 0.5, "Should have reasonable confidence"
        assert any(word in analysis.keywords for word in ["trapped", "dark", "scared"])
    
    def test_static_dream_analysis(self):
        """Test analysis of a static dream."""
        dream_text = "I was sitting peacefully by a calm lake, watching the still water"
        analysis = self.analyser.analyze_dream(dream_text)
        
        assert analysis.static_dynamic_score <= 0, "Should be static"
        assert any(word in analysis.keywords for word in ["sitting", "peaceful", "calm", "still"])
    
    def test_empty_dream_handling(self):
        """Test handling of very short or empty dreams."""
        analysis = self.analyser.analyze_dream("I slept.")
        
        assert -1 <= analysis.upper_downer_score <= 1
        assert -1 <= analysis.static_dynamic_score <= 1
        assert 0 <= analysis.confidence <= 1
    
    def test_keyword_extraction(self):
        """Test keyword extraction functionality."""
        dream_text = "I was running and jumping, feeling very happy and energetic"
        analysis = self.analyser.analyze_dream(dream_text)
        
        expected_keywords = {"running", "jumping", "happy"}
        found_keywords = set(analysis.keywords)
        
        assert expected_keywords.intersection(found_keywords), "Should find relevant keywords"