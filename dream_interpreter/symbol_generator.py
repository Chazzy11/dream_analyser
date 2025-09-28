import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image as PILImage, ImageDraw
import io
import base64
import logging
from typing import List, Tuple
from .models import DreamRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SymbolGenerator:
    """Generates evolving symbols based on dream analysis."""
    
    def __init__(self):
        self.colors = {
            'upper': ['#FFD700', '#FFA500', '#FF69B4', '#00CED1'],  # Gold, orange, pink, turquoise
            'downer': ['#800080', '#4B0082', '#191970', '#2F4F4F'],  # Purple, indigo, navy, dark slate
            'dynamic': ['#FF4500', '#DC143C', '#B22222'],  # Red spectrum
            'static': ['#4682B4', '#6495ED', '#87CEEB']   # Blue spectrum
        }
    
    def generate_symbol(self, dreams: List[DreamRecord]) -> str:
        """Generate a symbol based on all user dreams."""
        try:
            logger.info(f"Starting symbol generation for {len(dreams)} dreams")

            if not dreams:
                logger.warning("No dreams provided, generating base symbol.")
                return self._create_base_symbol()
        
            # Calculate average position and create symbol
            avg_x, avg_y = self._calculate_average_position(dreams)
            symbol_complexity = min(len(dreams), 10)  # Cap complexity at 10 dreams

            logger.info(f"Average position: ({avg_x:.2f}, {avg_y:.2f}), Complexity: {symbol_complexity}")
        
            # Create the symbol
            fig, ax = plt.subplots(1, 1, figsize=(6, 6))
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            ax.set_aspect('equal')
            ax.axis('off')
        
            # Set background color based on dominant emotional tone
            bg_color = self._get_background_color(avg_y)
            fig.patch.set_facecolor(bg_color)
        
            # Draw the evolving symbol
            self._draw_symbol_layers(ax, dreams, avg_x, avg_y, symbol_complexity)
        
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', 
                    facecolor=bg_color, edgecolor='none', dpi=150)
            plt.close(fig)
            
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            logger.info("Symbol generation completed successfully.")
            return image_base64
        
        except Exception as e:
            logger.error(f"Error generating symbol: {e}")
            return self._create_error_symbol()
    
    def _calculate_average_position(self, dreams: List[DreamRecord]) -> Tuple[float, float]:
        """Calculate the average position of all dreams."""
        x_coords = [dream.analysis.static_dynamic_score for dream in dreams]
        y_coords = [dream.analysis.upper_downer_score for dream in dreams]
        
        return np.mean(x_coords), np.mean(y_coords)
    
    def _get_background_color(self, avg_y: float) -> str:
        """Get background color based on emotional tone."""
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
        try:
            base_color = self._get_primary_color(avg_x, avg_y)
            base_circle = patches.Circle((0, 0), 0.3, facecolor=base_color, 
                                    edgecolor='white', linewidth=2, alpha=0.8)
            ax.add_patch(base_circle)
            
            # Add layers for each dream (up to complexity limit)
            for i, dream in enumerate(dreams[:complexity]):
                self._add_dream_layer(ax, dream, i, complexity)
            
            # Add central symbol based on dominant characteristics
            self._add_central_symbol(ax, avg_x, avg_y)
        
        except Exception as e:
            logger.error(f"Error drawing symbol layers: {e}")
    
    def _get_primary_color(self, x: float, y: float) -> str:
        """Get primary color based on coordinates."""
        try:
            if y > 0:  # Upper
                if x > 0:  # Dynamic upper
                    return self.colors['upper'][0]  # Gold
                else:  # Static upper
                    return self.colors['upper'][3]  # Turquoise
            else:  # Downer
                if x > 0:  # Dynamic downer
                    return self.colors['downer'][0]  # Purple
                else:  # Static downer
                    return self.colors['downer'][2]  # Navy
        
        except Exception as e:
            logger.error(f"Error selecting primary color: {e}")
            return '#808080'  # Fallback to gray
    
    def _add_dream_layer(self, ax, dream: DreamRecord, layer_index: int, total_layers: int):
        """Add a layer representing a single dream."""
        try:
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
                    triangle = patches.RegularPolygon((pos_x, pos_y), 3, 
                                                    radius=0.1, 
                                                    facecolor=self._get_dream_color(x, y),
                                                    alpha=0.7)
                    ax.add_patch(triangle)
                else:  # Static - use squares
                    square = patches.Rectangle((pos_x-0.05, pos_y-0.05), 0.1, 0.1,
                                            facecolor=self._get_dream_color(x, y),
                                            alpha=0.7)
                    ax.add_patch(square)
            else:  # More emotional than dynamic
                circle = patches.Circle((pos_x, pos_y), 0.05, 
                                    facecolor=self._get_dream_color(x, y),
                                    alpha=0.7)
                ax.add_patch(circle)
        except Exception as e:
            logger.error(f"Error adding dream layer: {layer_index}: {str(e)}")
    
    def _get_dream_color(self, x: float, y: float) -> str:
        """Get color for individual dream based on its coordinates."""
        try:
            if y > 0:
                colors = self.colors['upper']
            else:
                colors = self.colors['downer']
            
            # Pick color based on intensity
            intensity = (abs(y) + abs(x)) / 2
            color_index = min(int(intensity * len(colors)), len(colors) - 1)
            return colors[color_index]
        except Exception as e:
            logger.error(f"Error selecting dream color: {e}")
            return '#808080'  # Fallback to gray
    
    def _add_central_symbol(self, ax, avg_x: float, avg_y: float):
        """Add a central symbol representing the overall dream pattern."""
        try:
            if avg_y > 0.5:  # Very positive
                # Add a star
                star = patches.RegularPolygon((0, 0), 5, 
                                              radius=0.15, 
                                              facecolor='white', 
                                              edgecolor='gold', 
                                              linewidth=2)
                ax.add_patch(star)
            elif avg_y < -0.5:  # Very negative
                # Add a darker center
                center = patches.Circle((0, 0), 0.1, facecolor='black', alpha=0.8)
                ax.add_patch(center)
            
            if abs(avg_x) > 0.5:  # Very dynamic or static
                # Add radiating lines
                for angle in np.linspace(0, 2*np.pi, 8, endpoint=False):
                    line_length = 0.2 if avg_x > 0 else 0.15  # Longer lines for dynamic
                    end_x = line_length * np.cos(angle)
                    end_y = line_length * np.sin(angle)
                    ax.plot([0, end_x], [0, end_y], 'white', linewidth=2, alpha=0.8)
        
        except Exception as e:
            logger.error(f"Error adding central symbol: {e}")

    def _create_base_symbol(self) -> str:
        """Create a base symbol for new users."""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(6, 6))
            ax.set_xlim(-1.5, 1.5)
            ax.set_ylim(-1.5, 1.5)
            ax.set_aspect('equal')
            ax.axis('off')
            fig.patch.set_facecolor('#F5F5F5')
            
            # Simple circle for new dreamers
            circle = patches.Circle((0, 0), 0.3, facecolor='lightgray', 
                                edgecolor='white', linewidth=2, alpha=0.8)
            ax.add_patch(circle)
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', 
                    facecolor='#F5F5F5', edgecolor='none', dpi=150)
            plt.close(fig)
            
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error creating base symbol: {e}")
            return self._create_error_symbol()
        
    def _create_error_symbol(self) -> str:
        """Create a simple error symbol when matplotlib fails."""
        try:
            # Create a minimal 100x100 white image with a simple pattern
            
            img = PILImage.new('RGB', (100, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw a simple circle
            draw.ellipse([25, 25, 75, 75], fill='lightblue', outline='black')
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception:
            # Last resort: return a tiny transparent image
            return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="