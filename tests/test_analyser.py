from unittest.mock import AsyncMock, MagicMock

import pytest

from dream_interpreter.analyser import Dreamanalyser, LLMDreamanalyser
from dream_interpreter.models import DreamAnalysis


class TestDreamanalyser:
    """Test cases for the Dreamanalyser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyser = Dreamanalyser()

    def test_positive_dream_analysis(self):
        """Test analysis of a positive dream."""
        dream_text = (
            "I was flying through beautiful golden clouds, feeling happy and free"
        )
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
        assert any(
            word in analysis.keywords
            for word in ["sitting", "peaceful", "calm", "still"]
        )

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

        assert expected_keywords.intersection(
            found_keywords
        ), "Should find relevant keywords"


class TestLLMDreamanalyser:
    """Test cases for the LLMDreamanalyser class."""

    def setup_method(self):
        """Set up test fixtures with a mock Anthropic client to avoid real API calls."""
        self.mock_client = MagicMock()
        self.analyser = LLMDreamanalyser(anthropic_client=self.mock_client)

    def _make_mock_response(
        self,
        upper_downer: float = 0.5,
        static_dynamic: float = 0.5,
        confidence: float = 0.8,
        keywords: list = None,
    ) -> MagicMock:
        """Build a fake Anthropic tool-use response."""
        mock_tool_use = MagicMock()
        mock_tool_use.input = {
            "upper_downer_score": upper_downer,
            "static_dynamic_score": static_dynamic,
            "confidence": confidence,
            "keywords": keywords or [],
        }
        mock_message = MagicMock()
        mock_message.content = [mock_tool_use]
        return mock_message

    @pytest.mark.asyncio
    async def test_analyze_dream_returns_dream_analysis_type(self):
        """analyze_dream should return a DreamAnalysis instance."""
        self.mock_client.messages.create = AsyncMock(
            return_value=self._make_mock_response()
        )
        result = await self.analyser.analyze_dream("I was flying through clouds")
        assert isinstance(result, DreamAnalysis)

    @pytest.mark.asyncio
    async def test_analyze_dream_maps_tool_output_to_scores(self):
        """Scores from the API tool response should be passed through unchanged."""
        self.mock_client.messages.create = AsyncMock(
            return_value=self._make_mock_response(
                upper_downer=0.7,
                static_dynamic=-0.3,
                confidence=0.9,
                keywords=["labyrinth", "ouroboros"],
            )
        )
        result = await self.analyser.analyze_dream("I wandered a labyrinth")
        assert result.upper_downer_score == 0.7
        assert result.static_dynamic_score == -0.3
        assert result.confidence == 0.9
        assert result.keywords == ["labyrinth", "ouroboros"]

    @pytest.mark.asyncio
    async def test_analyze_dream_passes_dream_text_as_user_message(self):
        """The dream text should be sent as the user message to the API."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.messages.create = mock_create

        dream_text = "A very specific dream description for testing"
        await self.analyser.analyze_dream(dream_text)

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["messages"][0]["content"] == dream_text

    @pytest.mark.asyncio
    async def test_analyze_dream_forces_tool_use(self):
        """tool_choice should be set to 'any' to prevent free-text responses."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.messages.create = mock_create

        await self.analyser.analyze_dream("some dream")

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "any"}

    @pytest.mark.asyncio
    async def test_analyze_dream_uses_zero_temperature(self):
        """temperature=0 should be set for reproducible results in tests."""
        mock_create = AsyncMock(return_value=self._make_mock_response())
        self.mock_client.messages.create = mock_create

        await self.analyser.analyze_dream("some dream")

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["temperature"] == 0

    @pytest.mark.asyncio
    async def test_analyze_dream_score_boundary_negative(self):
        """Scores at the negative boundary (-1.0) should be accepted."""
        self.mock_client.messages.create = AsyncMock(
            return_value=self._make_mock_response(
                upper_downer=-1.0, static_dynamic=-1.0
            )
        )
        result = await self.analyser.analyze_dream("nightmare")
        assert result.upper_downer_score == -1.0
        assert result.static_dynamic_score == -1.0

    @pytest.mark.asyncio
    async def test_analyze_dream_score_boundary_positive(self):
        """Scores at the positive boundary (1.0) should be accepted."""
        self.mock_client.messages.create = AsyncMock(
            return_value=self._make_mock_response(upper_downer=1.0, static_dynamic=1.0)
        )
        result = await self.analyser.analyze_dream("bliss")
        assert result.upper_downer_score == 1.0
        assert result.static_dynamic_score == 1.0

    @pytest.mark.asyncio
    async def test_analyze_dream_accepts_novel_keywords(self):
        """Keywords not in the legacy word list should be returned without filtering."""
        novel_keywords = ["ouroboros", "labyrinth", "chrysalis", "doppelganger"]
        self.mock_client.messages.create = AsyncMock(
            return_value=self._make_mock_response(keywords=novel_keywords)
        )
        result = await self.analyser.analyze_dream(
            "I encountered an ouroboros inside a labyrinth"
        )
        assert result.keywords == novel_keywords
