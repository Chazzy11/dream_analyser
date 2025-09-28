import pytest
from fastapi.testclient import TestClient

from dream_interpreter.main import app


class TestAPI:
    """Test cases for the FastAPI application."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test the root endpoint returns HTML."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "Dream Interpreter" in response.text

    def test_analyze_dream_endpoint(self):
        """Test dream analysis endpoint."""
        dream_data = {
            "dream_text": "I was flying over a beautiful landscape feeling free and happy",
            "user_id": "test_user",
        }

        response = self.client.post("/analyze-dream", json=dream_data)
        assert response.status_code == 200

        data = response.json()
        assert "analysis" in data
        assert "upper_downer_score" in data["analysis"]
        assert "static_dynamic_score" in data["analysis"]
        assert "confidence" in data["analysis"]
        assert "keywords" in data["analysis"]

    def test_analyze_short_dream(self):
        """Test analysis of a very short dream."""
        dream_data = {"dream_text": "I fell down.", "user_id": "test_user"}

        response = self.client.post("/analyze-dream", json=dream_data)
        assert response.status_code == 200

    def test_generate_symbol_endpoint(self):
        """Test symbol generation endpoint."""
        # First analyze a dream
        dream_data = {
            "dream_text": "I was swimming in clear blue water, feeling peaceful and calm",
            "user_id": "symbol_test_user",
        }

        self.client.post("/analyze-dream", json=dream_data)

        # Then generate symbol
        response = self.client.get("/generate-symbol/symbol_test_user")
        assert response.status_code == 200

        data = response.json()
        assert "symbol_base64" in data
        assert "dream_count" in data
        assert "coordinates" in data
        assert data["dream_count"] >= 1

    def test_user_stats_endpoint(self):
        """Test user statistics endpoint."""
        # Analyze multiple dreams first
        dreams = [
            "I was flying through the clouds feeling amazing",
            "I was running fast through a forest",
            "I was sitting quietly by a lake",
        ]

        for dream in dreams:
            dream_data = {"dream_text": dream, "user_id": "stats_test_user"}
            self.client.post("/analyze-dream", json=dream_data)

        # Get stats
        response = self.client.get("/user-stats/stats_test_user")
        assert response.status_code == 200

        data = response.json()
        assert "total_dreams" in data
        assert data["total_dreams"] >= 3
        assert "average_emotional_score" in data
        assert "average_dynamic_score" in data
        assert "dominant_quadrant" in data

    def test_invalid_dream_input(self):
        """Test handling of invalid dream input."""
        dream_data = {"dream_text": "", "user_id": "test_user"}  # Empty dream

        response = self.client.post("/analyze-dream", json=dream_data)
        assert response.status_code == 422  # Validation error

    def test_nonexistent_user_stats(self):
        """Test stats for user with no dreams."""
        response = self.client.get("/user-stats/nonexistent_user")
        assert response.status_code == 200

        data = response.json()
        assert data["total_dreams"] == 0
