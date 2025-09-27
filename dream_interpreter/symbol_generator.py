import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import io
import base64
from typing import List, Tuple
from .models import DreamRecord


class SymbolGenerator:
    """Generates evolving symbols based on dream analysis."""
    
    def __init__(self):
        self.colours = {
            'upper': ['#FFD700', '#FFA500', '#FF69B4', '#00CED1'],  # Gold, orange, pink, turquoise
            'downer': ['#800080', '#4B0082', '#191970', '#2F4F4F'],  # Purple, indigo, navy, dark slate
            'dynamic': ['#FF4500', '#DC143C', '#B22222'],  # Red spectrum
            'static': ['#4682B4', '#6495ED', '#87CEEB']   # Blue spectrum
        }
    
    def generate_symbol(self, dreams: List[DreamRecord]) -> str:
        """Generate a symbol based on all user dreams."""
        if not dreams:
            return self._create_base_symbol()
        
        # Calculate average position and create symbol
        avg_x, avg_y = self._calculate_average_position(dreams)
        symbol_complexity = min(len(dreams), 10)  # Cap complexity at 10 dreams
        
        # Create the symbol
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Set background colour based on dominant emotional tone
        bg_colour = self._get_background_colour(avg_y)
        fig.patch.set_facecolour(bg_colour)
        
        # Draw the evolving symbol
        self._draw_symbol_layers(ax, dreams, avg_x, avg_y, symbol_complexity)
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', 
                   facecolour=bg_colour, edgecolour='none', dpi=150)
        plt.close()
        
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
    
    def _calculate_average_position(self, dreams: List[DreamRecord]) -> Tuple[float, float]:
        """Calculate the average position of all dreams."""
        x_coords = [dream.analysis.static_dynamic_score for dream in dreams]
        y_coords = [dream.analysis.upper_downer_score for dream in dreams]
        
        return np.mean(x_coords), np.mean(y_coords)
    
    def _get_background_colour(self, avg_y: float) -> str:
        """Get background colour based on emotional tone."""
        if avg_y > 0.3:
            return '#FFF8DC'  # Cornsilk (light, positive)
        elif avg_y < -0.3:
            return '#2F2F2F'  # Dark gray (darker, negative)
        else:
            return '#F5F5F5'  # Light gray (neutral)
    
    def _draw_symbol_layers(self, ax, dreams: List[DreamRecord], avg_x: float, 
                           avg_y: float, complexity: int):
        """Draw the layered symbol based on dreams."""
        # Base circle representing the dreamer's core
        base_colour = self._get_primary_colour(avg_x, avg_y)
        base_circle = patches.Circle((0, 0), 0.3, facecolour=base_colour, 
                                   edgecolour='white', linewidth=2, alpha=0.8)
        ax.add_patch(base_circle)
        
        # Add layers for each dream (up to complexity limit)
        for i, dream in enumerate(dreams[:complexity]):
            self._add_dream_layer(ax, dream, i, complexity)
        
        # Add central symbol based on dominant characteristics
        self._add_central_symbol(ax, avg_x, avg_y)
    
    def _get_primary_colour(self, x: float, y: float) -> str:
        """Get primary colour based on coordinates."""
        if y > 0:  # Upper
            if x > 0:  # Dynamic upper
                return self.colours['upper'][0]  # Gold
            else:  # Static upper
                return self.colours['upper'][3]  # Turquoise
        else:  # Downer
            if x > 0:  # Dynamic downer
                return self.colours['downer'][0]  # Purple
            else:  # Static downer
                return self.colours['downer'][2]  # Navy
    
    def _add_dream_layer(self, ax, dream: DreamRecord, layer_index: int, total_layers: int):
        """Add a layer representing a single dream."""
        x = dream.analysis.static_dynamic_score
        y = dream.analysis.upper_downer_score
        
        # Calculate position around the base circle
        angle = (2 * np.pi * layer_index) / total_layers
        radius = 0.5 + (layer_index * 0.1)  # Expanding outward
        
        pos_x = radius * np.cos(angle) * 0.5  # Scale down
        pos_y = radius * np.sin(angle) * 0.5
        
        # Choose shape based on dream characteristics
        if abs(x) > abs(y):  # More dynamic/static than upper/downer
            if x > 0:  # Dynamic - use triangles
                triangle = patches.RegularPolygon((pos_x, pos_y), 3, 0.1, 
                                                facecolour=self._get_dream_colour(x, y),
                                                alpha=0.7)
                ax.add_patch(triangle)
            else:  # Static - use squares
                square = patches.Rectangle((pos_x-0.05, pos_y-0.05), 0.1, 0.1,
                                         facecolour=self._get_dream_colour(x, y),
                                         alpha=0.7)
                ax.add_patch(square)
        else:  # More emotional than dynamic
            circle = patches.Circle((pos_x, pos_y), 0.05, 
                                  facecolour=self._get_dream_colour(x, y),
                                  alpha=0.7)
            ax.add_patch(circle)
    
    def _get_dream_colour(self, x: float, y: float) -> str:
        """Get colour for individual dream based on its coordinates."""
        if y > 0:
            colours = self.colours['upper']
        else:
            colours = self.colours['downer']
        
        # Pick colour based on intensity
        intensity = (abs(y) + abs(x)) / 2
        colour_index = min(int(intensity * len(colours)), len(colours) - 1)
        return colours[colour_index]
    
    def _add_central_symbol(self, ax, avg_x: float, avg_y: float):
        """Add a central symbol representing the overall dream pattern."""
        if avg_y > 0.5:  # Very positive
            # Add a star
            star = patches.RegularPolygon((0, 0), 5, 0.15, facecolour='white', 
                                        edgecolour='gold', linewidth=2)
            ax.add_patch(star)
        elif avg_y < -0.5:  # Very negative
            # Add a darker center
            center = patches.Circle((0, 0), 0.1, facecolour='black', alpha=0.8)
            ax.add_patch(center)
        
        if abs(avg_x) > 0.5:  # Very dynamic or static
            # Add radiating lines
            for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
                line_length = 0.2 if avg_x > 0 else 0.15  # Longer lines for dynamic
                end_x = line_length * np.cos(angle)
                end_y = line_length * np.sin(angle)
                ax.plot([0, end_x], [0, end_y], 'white', linewidth=2, alpha=0.8)
    
    def _create_base_symbol(self) -> str:
        """Create a base symbol for new users."""
        fig, ax = plt.subplots(1, 1, figsize=(6, 6))
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        fig.patch.set_facecolour('#F5F5F5')
        
        # Simple circle for new dreamers
        circle = patches.Circle((0, 0), 0.3, facecolour='lightgray', 
                              edgecolour='white', linewidth=2, alpha=0.8)
        ax.add_patch(circle)
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', 
                   facecolour='#F5F5F5', edgecolour='none', dpi=150)
        plt.close()
        
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')