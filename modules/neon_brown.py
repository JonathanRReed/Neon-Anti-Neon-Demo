"""
Neon Brown Module - Context-Induced Brown/Orange Color Shift

This module demonstrates how the same orange patch can appear "brown" when 
surrounded by a bright surround, due to center-surround contrast effects.

Key scientific points:
- Brown is a context-dependent color (not a spectral color)
- The same RGB values can be perceived as orange OR brown
- Surround luminance is the primary factor shifting perception
- This is NOT fluorescence - displays can't do that

References:
- Brown perception depends on center-surround luminance contrast
- The brown-orange boundary shifts with context
"""

import numpy as np
from typing import Tuple, Optional, Dict
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from color_management import ColorManagement, ColorAppearance, srgb_to_linear, linear_to_srgb
from modules import register_module


@dataclass
class NeonBrownParams:
    """Parameters for the neon brown illusion."""
    # Center patch parameters
    center_hue: float = 30.0  # Degrees (orange range: 15-45)
    center_saturation: float = 0.7
    center_luminance: float = 0.35  # Lower luminance for brown potential
    
    # Surround parameters for each panel
    dim_surround_luminance: float = 0.15  # Dark surround -> looks orange
    bright_surround_luminance: float = 0.85  # Bright surround -> looks brown
    
    # Edge conditions
    edge_type: str = "thin_border"  # "none", "thin_border", "gap"
    border_luminance: float = 0.0  # Black border
    gap_width: int = 5
    
    # Display options
    show_proof_overlay: bool = True
    center_patch_size: int = 100  # Pixels


@register_module
class NeonBrownModule:
    """
    Interactive demonstration of context-induced brown/orange perception.
    
    Shows two identical center patches on different surrounds to demonstrate
    how the same color can appear orange or brown based on context.
    """
    
    def __init__(self, params: Optional[NeonBrownParams] = None):
        self.params = params or NeonBrownParams()
        self._center_rgb: Optional[Tuple[float, float, float]] = None
    
    @property
    def name(self) -> str:
        return "Neon Brown: Context-Induced Color Shift"
    
    @property
    def description(self) -> str:
        return (
            "The same orange patch appears 'brown' on a bright surround. "
            "This demonstrates that brown is a context-dependent percept, "
            "not a spectral color. Both center patches have IDENTICAL RGB values."
        )
    
    @property
    def has_safety_warning(self) -> bool:
        return False  # Safe for all viewers
    
    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[float, float, float]:
        """
        Convert HSL to RGB (for better luminance control than HSV).
        
        Args:
            h: Hue in degrees (0-360)
            s: Saturation (0-1)
            l: Luminance/Lightness (0-1)
            
        Returns:
            RGB tuple (0-1 range)
        """
        h = h % 360
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l - c / 2
        
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return (r + m, g + m, b + m)
    
    def get_center_rgb(self) -> Tuple[float, float, float]:
        """Get the RGB values of the center patch."""
        if self._center_rgb is None:
            self._center_rgb = self._hsl_to_rgb(
                self.params.center_hue,
                self.params.center_saturation,
                self.params.center_luminance
            )
        return self._center_rgb
    
    def invalidate_cache(self):
        """Call when params change to recompute colors."""
        self._center_rgb = None
    
    def render_single_panel(
        self,
        width: int,
        height: int,
        surround_luminance: float
    ) -> np.ndarray:
        """
        Render a single panel with center patch on surround.
        
        Args:
            width: Panel width in pixels
            height: Panel height in pixels
            surround_luminance: Luminance of the surround (0-1)
            
        Returns:
            Rendered panel as (H, W, 3) array
        """
        # Create surround (gray at specified luminance)
        panel = np.full((height, width, 3), surround_luminance, dtype=np.float32)
        
        # Calculate center patch position
        patch_size = self.params.center_patch_size
        cx = width // 2
        cy = height // 2
        x1 = cx - patch_size // 2
        y1 = cy - patch_size // 2
        x2 = x1 + patch_size
        y2 = y1 + patch_size
        
        # Handle edge conditions
        if self.params.edge_type == "gap":
            # Leave a gap (surround color) between patch and surround
            gap = self.params.gap_width
            x1 += gap
            y1 += gap
            x2 -= gap
            y2 -= gap
        elif self.params.edge_type == "thin_border":
            # Draw a thin border around the patch
            border_width = 2
            panel[y1-border_width:y2+border_width, x1-border_width:x2+border_width] = \
                self.params.border_luminance
        
        # Draw center patch
        center_rgb = self.get_center_rgb()
        panel[y1:y2, x1:x2, 0] = center_rgb[0]
        panel[y1:y2, x1:x2, 1] = center_rgb[1]
        panel[y1:y2, x1:x2, 2] = center_rgb[2]
        
        return panel
    
    def render(self, width: int, height: int) -> np.ndarray:
        """
        Render the full two-panel display.
        
        Left panel: dim surround (orange appearance)
        Right panel: bright surround (brown appearance)
        
        Args:
            width: Total width in pixels
            height: Total height in pixels
            
        Returns:
            Rendered image as (H, W, 3) array
        """
        # Split width between two panels with small gap
        gap = 10
        panel_width = (width - gap) // 2
        
        # Render both panels
        left_panel = self.render_single_panel(
            panel_width, height,
            self.params.dim_surround_luminance
        )
        right_panel = self.render_single_panel(
            panel_width, height,
            self.params.bright_surround_luminance
        )
        
        # Create gap (black)
        gap_strip = np.zeros((height, gap, 3), dtype=np.float32)
        
        # Combine
        result = np.concatenate([left_panel, gap_strip, right_panel], axis=1)
        
        return result
    
    def get_proof_info(self) -> str:
        """Get proof text showing both patches are identical."""
        center_rgb = self.get_center_rgb()
        hex_color = ColorManagement.rgb_to_hex(np.array(center_rgb))
        rgb_8bit = tuple(int(v * 255) for v in center_rgb)
        
        # Predict brown probability for each surround
        p_brown_dim = ColorAppearance.predict_brown_probability(
            self.params.center_hue,
            self.params.center_saturation,
            self.params.center_luminance,
            self.params.dim_surround_luminance
        )
        p_brown_bright = ColorAppearance.predict_brown_probability(
            self.params.center_hue,
            self.params.center_saturation,
            self.params.center_luminance,
            self.params.bright_surround_luminance
        )
        
        return (
            f"--- PIXEL PROOF ---\n"
            f"Both center patches are IDENTICAL:\n"
            f"  HEX: {hex_color}\n"
            f"  RGB: {rgb_8bit}\n"
            f"  sRGB: ({center_rgb[0]:.3f}, {center_rgb[1]:.3f}, {center_rgb[2]:.3f})\n"
            f"\n"
            f"Predicted perception:\n"
            f"  Dim surround → P(brown) = {p_brown_dim:.1%}\n"
            f"  Bright surround → P(brown) = {p_brown_bright:.1%}"
        )
    
    def get_explanation(self) -> str:
        """Get scientific explanation of the effect."""
        return (
            "WHY DOES THIS WORK?\n"
            "-------------------\n"
            "\n"
            "Brown is NOT a spectral color - you cannot create 'brown light'.\n"
            "Brown is perceived when:\n"
            "  1. The hue is in the orange/yellow-orange range\n"
            "  2. The PERCEIVED lightness is low relative to surroundings\n"
            "\n"
            "A bright surround makes the center patch APPEAR darker,\n"
            "shifting perception from 'orange' to 'brown' even though\n"
            "the physical light hasn't changed.\n"
            "\n"
            "This is called SIMULTANEOUS CONTRAST - your visual system\n"
            "perceives colors relative to their context, not absolutely.\n"
            "\n"
            "IMPORTANT: Displays cannot create 'fluorescent' colors.\n"
            "Fluorescence involves wavelength conversion (absorbing UV,\n"
            "emitting visible light) which RGB displays cannot do."
        )
    
    def update_params(self, **kwargs) -> None:
        """Update parameters and invalidate cache."""
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
        self.invalidate_cache()
    
    def get_experiment_conditions(self) -> Dict:
        """Get structured information for experiment logging."""
        return {
            'module': 'NeonBrown',
            'center_hue': self.params.center_hue,
            'center_saturation': self.params.center_saturation,
            'center_luminance': self.params.center_luminance,
            'dim_surround': self.params.dim_surround_luminance,
            'bright_surround': self.params.bright_surround_luminance,
            'edge_type': self.params.edge_type,
            'center_rgb': self.get_center_rgb()
        }


# Convenience function to create standard demo
def create_neon_brown_demo() -> NeonBrownModule:
    """Create a NeonBrownModule with default settings."""
    return NeonBrownModule()


# Test the module
if __name__ == "__main__":
    # Quick visual test
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    module = NeonBrownModule()
    
    # Render
    image = module.render(800, 400)
    
    # Show proof info
    print(module.get_proof_info())
    print()
    print(module.get_explanation())
    
    # Save test image
    plt.figure(figsize=(12, 6))
    plt.imshow(image)
    plt.title(module.name)
    plt.axis('off')
    
    # Add proof text
    proof = module.get_proof_info().split('\n')
    for i, line in enumerate(proof):
        plt.text(400, 20 + i * 15, line, fontsize=8, ha='center', color='white',
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    plt.savefig('neon_brown_test.png', dpi=150, bbox_inches='tight')
    print("\nSaved test image to neon_brown_test.png")
