"""Symbol generation using either DALL-E 3 or a legacy matplotlib fallback."""
import base64
import io
import logging
from typing import List, Tuple

import matplotlib

matplotlib.use("Agg")  # Must be called before importing pyplot
import matplotlib.patches as patches  # pylint: disable=wrong-import-position
import matplotlib.pyplot as plt  # pylint: disable=wrong-import-position
import numpy as np  # pylint: disable=wrong-import-position
from openai import AsyncOpenAI  # pylint: disable=wrong-import-position
from PIL import Image as PILImage  # pylint: disable=wrong-import-position
from PIL import ImageDraw  # pylint: disable=wrong-import-position

from .models import DreamRecord  # pylint: disable=wrong-import-position

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AISymbolGenerator:  # pylint: disable=too-few-public-methods
    """Generates dream symbols using DALL-E 3 image generation."""

    def __init__(self, openai_client: AsyncOpenAI = None):
        """Initialise the generator.

        Args:
            openai_client: Optional pre-built AsyncOpenAI client (useful for testing).
        """
        self._client = openai_client or AsyncOpenAI()
        self._legacy = LegacySymbolGenerator()

    async def generate_symbol(self, dreams: List[DreamRecord]) -> str:
        """Generate a DALL-E 3 image symbol based on the user's dreams.

        Falls back to the legacy matplotlib generator when the dream list is
        empty or if the OpenAI API call fails.

        Args:
            dreams: All dream records for the user.

        Returns:
            Base64-encoded PNG string.
        """
        if not dreams:
            return self._legacy.generate_symbol(dreams)

        # Average scores across all dreams so the symbol reflects cumulative history.
        avg_upper_downer = sum(d.analysis.upper_downer_score for d in dreams) / len(
            dreams
        )
        avg_static_dynamic = sum(d.analysis.static_dynamic_score for d in dreams) / len(
            dreams
        )

        # Aggregate keywords most-recent-first so newer dreams take priority in the
        # 5-keyword prompt slot when the user has many dreams.
        seen: set = set()
        all_keywords: List[str] = []
        for dream in reversed(dreams):
            for kw in dream.analysis.keywords:
                if kw not in seen:
                    seen.add(kw)
                    all_keywords.append(kw)

        prompt = self._build_image_prompt(
            all_keywords,
            avg_upper_downer,
            avg_static_dynamic,
            len(dreams),
        )

        try:
            response = await self._client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                response_format="b64_json",
                n=1,
            )
            return response.data[0].b64_json
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("AI symbol generation failed, falling back to legacy: %s", e)
            return self._legacy.generate_symbol(dreams)

    def _build_image_prompt(
        self,
        keywords: List[str],
        upper_downer: float,
        static_dynamic: float,
        dream_count: int,
    ) -> str:
        """Build a DALL-E prompt from the dream's scores and keywords.

        Args:
            keywords: Significant dream elements extracted by the analyser.
            upper_downer: Emotional valence score (-1 to 1).
            static_dynamic: Energy level score (-1 to 1).
            dream_count: Total dreams logged by this user.

        Returns:
            A descriptive prompt string for DALL-E 3.
        """
        tone = (
            "luminous and uplifting"
            if upper_downer > 0.3
            else (
                "shadowy and melancholic"
                if upper_downer < -0.3
                else "mysterious and neutral"
            )
        )
        energy = (
            "swirling and kinetic"
            if static_dynamic > 0.3
            else ("still and contemplative" if static_dynamic < -0.3 else "balanced")
        )
        keyword_clause = f"incorporating {', '.join(keywords[:5])}" if keywords else ""
        complexity = f"complexity level {min(dream_count, 10)}/10"

        return (
            f"A symbolic mandala-like dream artwork, {tone}, {energy}, "
            f"{keyword_clause}. {complexity}. "
            "Digital art, intricate, dreamlike, no text."
        )


class LegacySymbolGenerator:
    """Generates evolving symbols based on dream analysis using matplotlib."""

    def __init__(self):
        """Initialise colour palettes."""
        self.colors = {
            "upper": [
                "#FFD700",
                "#FFA500",
                "#FF69B4",
                "#00CED1",
            ],  # Gold, orange, pink, turquoise
            "downer": [
                "#800080",
                "#4B0082",
                "#191970",
                "#2F4F4F",
            ],  # Purple, indigo, navy, dark slate
            "dynamic": ["#FF4500", "#DC143C", "#B22222"],  # Red spectrum
            "static": ["#4682B4", "#6495ED", "#87CEEB"],  # Blue spectrum
        }

    def generate_symbol(self, dreams: List[DreamRecord]) -> str:
        """Generate a symbol based on all user dreams.

        Args:
            dreams: All dream records for the user.

        Returns:
            Base64-encoded PNG string.
        """
        try:
            logger.info("Starting symbol generation for %s dreams", len(dreams))

            if not dreams:
                logger.warning("No dreams provided, generating base symbol.")
                return self._create_base_symbol()

            avg_x, avg_y = self._calculate_average_position(dreams)
            symbol_complexity = min(len(dreams), 10)

            logger.info(
                "Average position: (%.2f, %.2f), Complexity: %s",
                avg_x,
                avg_y,
                symbol_complexity,
            )

            fig, ax = plt.subplots(1, 1, figsize=(6, 6))
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            ax.set_aspect("equal")
            ax.axis("off")

            bg_color = self._get_background_color(avg_y)
            fig.patch.set_facecolor(bg_color)

            self._draw_symbol_layers(ax, dreams, avg_x, avg_y, symbol_complexity)

            buffer = io.BytesIO()
            plt.savefig(
                buffer,
                format="png",
                bbox_inches="tight",
                facecolor=bg_color,
                edgecolor="none",
                dpi=150,
            )
            plt.close(fig)

            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            logger.info("Symbol generation completed successfully.")
            return image_base64

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error generating symbol: %s", e)
            return self._create_error_symbol()

    def _calculate_average_position(
        self, dreams: List[DreamRecord]
    ) -> Tuple[float, float]:
        """Calculate the average position of all dreams."""
        x_coords = [dream.analysis.static_dynamic_score for dream in dreams]
        y_coords = [dream.analysis.upper_downer_score for dream in dreams]
        return np.mean(x_coords), np.mean(y_coords)

    def _get_background_color(self, avg_y: float) -> str:
        """Get background color based on emotional tone."""
        if avg_y > 0.3:
            return "#FFF8DC"  # Cornsilk (light, positive)
        if avg_y < -0.3:
            return "#2F2F2F"  # Dark gray (darker, negative)
        return "#F5F5F5"  # Light gray (neutral)

    def _draw_symbol_layers(
        self, ax, dreams: List[DreamRecord], avg_x: float, avg_y: float, complexity: int
    ):
        """Draw the layered symbol based on dreams."""
        try:
            base_color = self._get_primary_color(avg_x, avg_y)
            base_circle = patches.Circle(
                (0, 0),
                0.3,
                facecolor=base_color,
                edgecolor="white",
                linewidth=2,
                alpha=0.8,
            )
            ax.add_patch(base_circle)

            for i, dream in enumerate(dreams[:complexity]):
                self._add_dream_layer(ax, dream, i, complexity)

            self._add_central_symbol(ax, avg_x, avg_y)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error drawing symbol layers: %s", e)

    def _get_primary_color(self, x: float, y: float) -> str:
        """Get primary color based on coordinates."""
        try:
            if y > 0:
                return self.colors["upper"][0] if x > 0 else self.colors["upper"][3]
            return self.colors["downer"][0] if x > 0 else self.colors["downer"][2]
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error selecting primary color: %s", e)
            return "#808080"

    def _add_dream_layer(
        self, ax, dream: DreamRecord, layer_index: int, total_layers: int
    ):
        """Add a layer representing a single dream."""
        try:
            x = dream.analysis.static_dynamic_score
            y = dream.analysis.upper_downer_score

            angle = (2 * np.pi * layer_index) / total_layers
            radius = 0.5 + (layer_index * 0.1)

            pos_x = radius * np.cos(angle) * 0.5
            pos_y = radius * np.sin(angle) * 0.5

            if abs(x) > abs(y):
                if x > 0:
                    triangle = patches.RegularPolygon(
                        (pos_x, pos_y),
                        3,
                        radius=0.1,
                        facecolor=self._get_dream_color(x, y),
                        alpha=0.7,
                    )
                    ax.add_patch(triangle)
                else:
                    square = patches.Rectangle(
                        (pos_x - 0.05, pos_y - 0.05),
                        0.1,
                        0.1,
                        facecolor=self._get_dream_color(x, y),
                        alpha=0.7,
                    )
                    ax.add_patch(square)
            else:
                circle = patches.Circle(
                    (pos_x, pos_y),
                    0.05,
                    facecolor=self._get_dream_color(x, y),
                    alpha=0.7,
                )
                ax.add_patch(circle)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error adding dream layer %s: %s", layer_index, e)

    def _get_dream_color(self, x: float, y: float) -> str:
        """Get color for individual dream based on its coordinates."""
        try:
            colors = self.colors["upper"] if y > 0 else self.colors["downer"]
            intensity = (abs(y) + abs(x)) / 2
            color_index = min(int(intensity * len(colors)), len(colors) - 1)
            return colors[color_index]
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error selecting dream color: %s", e)
            return "#808080"

    def _add_central_symbol(self, ax, avg_x: float, avg_y: float):
        """Add a central symbol representing the overall dream pattern."""
        try:
            if avg_y > 0.5:
                star = patches.RegularPolygon(
                    (0, 0),
                    5,
                    radius=0.15,
                    facecolor="white",
                    edgecolor="gold",
                    linewidth=2,
                )
                ax.add_patch(star)
            elif avg_y < -0.5:
                center = patches.Circle((0, 0), 0.1, facecolor="black", alpha=0.8)
                ax.add_patch(center)

            if abs(avg_x) > 0.5:
                for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                    line_length = 0.2 if avg_x > 0 else 0.15
                    end_x = line_length * np.cos(angle)
                    end_y = line_length * np.sin(angle)
                    ax.plot([0, end_x], [0, end_y], "white", linewidth=2, alpha=0.8)

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error adding central symbol: %s", e)

    def _create_base_symbol(self) -> str:
        """Create a base symbol for new users."""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(6, 6))
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            ax.set_aspect("equal")
            ax.axis("off")
            fig.patch.set_facecolor("#F5F5F5")

            circle = patches.Circle(
                (0, 0),
                0.3,
                facecolor="lightgray",
                edgecolor="white",
                linewidth=2,
                alpha=0.8,
            )
            ax.add_patch(circle)

            buffer = io.BytesIO()
            plt.savefig(
                buffer,
                format="png",
                bbox_inches="tight",
                facecolor="#F5F5F5",
                edgecolor="none",
                dpi=150,
            )
            plt.close(fig)

            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error creating base symbol: %s", e)
            return self._create_error_symbol()

    def _create_error_symbol(self) -> str:
        """Create a minimal fallback symbol when matplotlib fails."""
        try:
            img = PILImage.new("RGB", (100, 100), color="white")
            draw = ImageDraw.Draw(img)
            draw.ellipse([25, 25, 75, 75], fill="lightblue", outline="black")

            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception:  # pylint: disable=broad-exception-caught
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


# Backward-compatibility alias — existing imports of SymbolGenerator still work.
SymbolGenerator = LegacySymbolGenerator
