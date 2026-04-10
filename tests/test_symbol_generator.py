from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from dream_interpreter.models import DreamAnalysis, DreamRecord
from dream_interpreter.symbol_generator import AISymbolGenerator, SymbolGenerator


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
        assert (
            symbol_base64.replace("+", "").replace("/", "").replace("=", "").isalnum()
        )

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
                keywords=["flying", "happy"],
            ),
            timestamp=datetime.now(),
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
                    keywords=[f"keyword{i}"],
                ),
                timestamp=datetime.now(),
            )
            dreams.append(dream)

        symbol_base64 = self.generator.generate_symbol(dreams)

        assert symbol_base64 is not None
        assert len(symbol_base64) > 0

    def test_color_selection(self):
        """Test that color selection works correctly."""
        # Test upper-right quadrant (positive, dynamic)
        color = self.generator._get_primary_color(0.5, 0.5)
        assert color in self.generator.colors["upper"]

        # Test lower-left quadrant (negative, static)
        color = self.generator._get_primary_color(-0.5, -0.5)
        assert color in self.generator.colors["downer"]


def _make_dream(
    upper_downer: float = 0.5,
    static_dynamic: float = 0.5,
    keywords: list = None,
) -> DreamRecord:
    """Build a minimal DreamRecord for testing."""
    return DreamRecord(
        id="test1",
        dream_text="A test dream",
        user_id="user1",
        analysis=DreamAnalysis(
            upper_downer_score=upper_downer,
            static_dynamic_score=static_dynamic,
            confidence=0.8,
            keywords=keywords or ["flying"],
        ),
        timestamp=datetime(2026, 1, 1),
    )


class TestAISymbolGenerator:
    """Test cases for the AISymbolGenerator class."""

    def setup_method(self):
        """Set up test fixtures with a mock OpenAI client."""
        self.mock_client = MagicMock()
        self.generator = AISymbolGenerator(openai_client=self.mock_client)

    def _make_mock_response(self, b64: str = "ZmFrZWltYWdl") -> MagicMock:
        """Build a fake OpenAI images.generate response."""
        mock_image = MagicMock()
        mock_image.b64_json = b64
        mock_response = MagicMock()
        mock_response.data = [mock_image]
        return mock_response

    @pytest.mark.asyncio
    async def test_generate_symbol_returns_base64_from_api(self):
        """generate_symbol should return the b64_json string from the API response."""
        self.mock_client.images.generate = AsyncMock(
            return_value=self._make_mock_response("ZmFrZWltYWdl")
        )
        result = await self.generator.generate_symbol([_make_dream()])
        assert result == "ZmFrZWltYWdl"

    @pytest.mark.asyncio
    async def test_generate_symbol_uses_dall_e_3(self):
        """generate_symbol should request a dall-e-3 image."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.images.generate = mock_create

        await self.generator.generate_symbol([_make_dream()])

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "dall-e-3"

    @pytest.mark.asyncio
    async def test_generate_symbol_requests_b64_json(self):
        """generate_symbol should request base64 response format, not a URL."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.images.generate = mock_create

        await self.generator.generate_symbol([_make_dream()])

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["response_format"] == "b64_json"

    @pytest.mark.asyncio
    async def test_generate_symbol_prompt_contains_keywords(self):
        """Prompt should include keywords aggregated across all dreams."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.images.generate = mock_create

        await self.generator.generate_symbol(
            [
                _make_dream(keywords=["labyrinth", "ouroboros"]),
                _make_dream(keywords=["chrysalis", "mirror"]),
            ]
        )

        prompt = mock_create.call_args.kwargs["prompt"]
        # Most-recent dream's keywords take priority in the 5-keyword slot
        assert "chrysalis" in prompt
        assert "mirror" in prompt

    @pytest.mark.asyncio
    async def test_generate_symbol_prompt_positive_tone(self):
        """Dreams with high upper_downer should produce an uplifting prompt."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.images.generate = mock_create

        await self.generator.generate_symbol([_make_dream(upper_downer=0.8)])

        prompt = mock_create.call_args.kwargs["prompt"]
        assert "luminous and uplifting" in prompt

    @pytest.mark.asyncio
    async def test_generate_symbol_prompt_negative_tone(self):
        """Dreams with low upper_downer should produce a melancholic prompt."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.images.generate = mock_create

        await self.generator.generate_symbol([_make_dream(upper_downer=-0.8)])

        prompt = mock_create.call_args.kwargs["prompt"]
        assert "shadowy and melancholic" in prompt

    @pytest.mark.asyncio
    async def test_generate_symbol_empty_dreams_uses_legacy(self):
        """An empty dream list should fall back to the legacy generator without an API call."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.images.generate = mock_create

        result = await self.generator.generate_symbol([])

        mock_create.assert_not_called()
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_symbol_falls_back_on_api_error(self):
        """An OpenAI API error should fall back to the legacy generator silently."""
        self.mock_client.images.generate = AsyncMock(side_effect=Exception("API error"))
        result = await self.generator.generate_symbol([_make_dream()])

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_symbol_uses_averaged_scores(self):
        """Scores should be averaged across all dreams, not taken from the last one."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.images.generate = mock_create

        # Two dreams with opposite tones — average is neutral, not uplifting or melancholic
        await self.generator.generate_symbol(
            [
                _make_dream(upper_downer=0.8),  # very positive
                _make_dream(upper_downer=-0.8),  # very negative
            ]
        )

        prompt = mock_create.call_args.kwargs["prompt"]
        assert "luminous and uplifting" not in prompt
        assert "shadowy and melancholic" not in prompt
        assert "mysterious and neutral" in prompt
