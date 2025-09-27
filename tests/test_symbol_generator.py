import pytest
from datetime import datetime
from dream_interpreter.symbol_generator import SymbolGenerator
from dream_interpreter.models import DreamRecord, DreamAnalysis


class TestSymbolGenerator:
    """Test cases for the SymbolGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SymbolGenerator()
    
    def test_base_symbol_generation(self):
        """Test generation of base symbol for new users."""
        symbol_base64 = self.generator.generate_symbol([])
        
        assert symbol_base64 is not None
        assert len(symbol_base64) > 0
        assert symbol_base64.replace('+', '').replace('/', '').replace('=', '').isalnum()
    
    def test_single_dream_symbol(self):
        """Test symbol generation with a single dream."""
        dream = DreamRecord(
            id="test1",
            dream_text="I was flying happily",
            user_id="test_user",
            analysis=DreamAnalysis(
                upper_downer_score=0.8,
                static_dynamic_score=0.6,
                confidence=0.9,
                keywords=["flying", "happy"]
            ),
            timestamp=datetime.now()
        )
        
        symbol_base64 = self.generator.generate_symbol([dream])
        
        assert symbol_base64 is not None
        assert len(symbol_base64) > 0
    
    def test_multiple_dreams_symbol(self):
        """Test symbol generation with multiple dreams."""
        dreams = []
        for i in range(5):
            dream = DreamRecord(
                id=f"test{i}",
                dream_text=f"Dream number {i}",
                user_id="test_user",
                analysis=DreamAnalysis(
                    upper_downer_score=0.2 * i - 0.4,  # Range from -0.4 to 0.4
                    static_dynamic_score=0.1 * i - 0.2,  # Range from -0.2 to 0.2
                    confidence=0.8,
                    keywords=[f"keyword{i}"]
                ),
                timestamp=datetime.now()
            )
            dreams.append(dream)
        
        symbol_base64 = self.generator.generate_symbol(dreams)
        
        assert symbol_base64 is not None
        assert len(symbol_base64) > 0
    
    def test_colour_selection(self):
        """Test that colour selection works correctly."""
        # Test upper-right quadrant (positive, dynamic)
        colour = self.generator._get_primary_colour(0.5, 0.5)
        assert colour in self.generator.colours['upper']
        
        # Test lower-left quadrant (negative, static)
        colour = self.generator._get_primary_colour(-0.5, -0.5)
        assert colour in self.generator.colours['downer']
