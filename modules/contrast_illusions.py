"""
Contrast Illusions Module - Simultaneous Contrast and Related Effects

This module implements several classic contrast and context illusions:
- Simultaneous Color Contrast
- Checker Shadow (Adelson's)
- Cornsweet Edge / Craik-O'Brien
- Chubb Illusion

Each illusion demonstrates how context affects perceived color/luminance.
"""

import numpy as np
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from color_management import ColorManagement, srgb_to_linear, linear_to_srgb
from modules import register_module


@dataclass
class SimultaneousContrastParams:
    """Parameters for simultaneous contrast demo.
    
    Classic effect: identical gray patches look different on 
    light vs dark backgrounds due to lateral inhibition.
    """
    target_gray: float = 0.5  # Target patch gray level (middle gray)
    surround1_color: Tuple[float, float, float] = (0.15, 0.15, 0.15)  # Dark surround
    surround2_color: Tuple[float, float, float] = (0.85, 0.85, 0.85)  # Light surround
    patch_size: int = 100  # Larger patches for clearer effect


@register_module
class SimultaneousContrastModule:
    """
    Simultaneous color/luminance contrast illusion.
    
    Two identical gray patches appear different on light vs dark surrounds.
    The patch on the dark surround appears lighter.
    """
    
    def __init__(self, params: Optional[SimultaneousContrastParams] = None):
        self.params = params or SimultaneousContrastParams()
    
    @property
    def name(self) -> str:
        return "Simultaneous Contrast"
    
    @property
    def description(self) -> str:
        return (
            "Two identical gray patches appear different based on their surrounds. "
            "The same gray looks lighter on a dark background and darker on a light background."
        )
    
    @property
    def has_safety_warning(self) -> bool:
        return False
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render the simultaneous contrast display."""
        gap = 10
        panel_width = (width - gap) // 2
        
        # Create panels with different surrounds
        left = np.zeros((height, panel_width, 3), dtype=np.float32)
        left[:, :, 0] = self.params.surround1_color[0]
        left[:, :, 1] = self.params.surround1_color[1]
        left[:, :, 2] = self.params.surround1_color[2]
        
        right = np.zeros((height, panel_width, 3), dtype=np.float32)
        right[:, :, 0] = self.params.surround2_color[0]
        right[:, :, 1] = self.params.surround2_color[1]
        right[:, :, 2] = self.params.surround2_color[2]
        
        # Add identical target patches
        ps = self.params.patch_size
        cx, cy = panel_width // 2, height // 2
        x1, y1 = cx - ps // 2, cy - ps // 2
        x2, y2 = x1 + ps, y1 + ps
        
        target_gray = self.params.target_gray
        left[y1:y2, x1:x2] = target_gray
        right[y1:y2, x1:x2] = target_gray
        
        # Combine with gap
        gap_strip = np.zeros((height, gap, 3), dtype=np.float32)
        result = np.concatenate([left, gap_strip, right], axis=1)
        
        return result
    
    def get_proof_info(self) -> str:
        """Proof that patches are identical."""
        g = self.params.target_gray
        hex_color = ColorManagement.rgb_to_hex(np.array([g, g, g]))
        return (
            f"--- PIXEL PROOF ---\n"
            f"Both target patches are IDENTICAL:\n"
            f"  Gray Level: {g:.3f}\n"
            f"  RGB 8-bit: ({int(g*255)}, {int(g*255)}, {int(g*255)})\n"
            f"  HEX: {hex_color}"
        )


@dataclass
class CheckerShadowParams:
    """Parameters for checker shadow illusion."""
    square_size: int = 40
    shadow_strength: float = 0.6


@register_module
class CheckerShadowModule:
    """
    Adelson's Checker Shadow Illusion.
    
    Squares A and B appear different but have identical luminance.
    The implied shadow context affects perceived lightness.
    
    Based on research: Both squares have RGB value {0.47, 0.47, 0.47}
    """
    
    def __init__(self, params: Optional[CheckerShadowParams] = None):
        self.params = params or CheckerShadowParams()
        # Exact value from Adelson's original:  {0.470588, 0.470588, 0.466667}
        self._target_value = 0.47  # Scientifically accurate value
    
    @property
    def name(self) -> str:
        return "Checker Shadow Illusion"
    
    @property
    def description(self) -> str:
        return (
            "Adelson's famous illusion: squares A and B appear very different, "
            "but they have IDENTICAL pixel values (RGB ~120, or 0.47). The implied "
            "shadow creates a context that shifts lightness perception."
        )
    
    @property
    def has_safety_warning(self) -> bool:
        return False
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render the checker shadow illusion - VECTORIZED."""
        sq = self.params.square_size
        shadow = self.params.shadow_strength
        
        # Checkerboard pattern with proper contrast
        light_square = 0.78
        dark_square = 0.35
        
        # Create coordinate grids
        y_coords, x_coords = np.ogrid[:height, :width]
        
        # Checkerboard pattern using modular arithmetic (fully vectorized)
        checker = ((x_coords // sq) + (y_coords // sq)) % 2 == 0
        image = np.where(checker, light_square, dark_square)
        image = np.stack([image, image, image], axis=-1).astype(np.float32)
        
        # Create a more realistic cylinder shadow (elliptical shape)
        # Shadow casts from top-right corner
        cx, cy = width * 0.6, height * 0.35
        
        # Create full coordinate arrays
        xx = np.arange(width).astype(np.float32)
        yy = np.arange(height).astype(np.float32)[:, np.newaxis]
        
        # Elliptical shadow gradient
        shadow_x = (xx - cx) / (width * 0.4)
        shadow_y = (yy - cy) / (height * 0.5)
        shadow_dist = np.sqrt(shadow_x**2 + shadow_y**2)
        
        # Soft shadow falloff
        in_shadow = shadow_dist < 1.0
        shadow_strength = np.clip(1.0 - shadow_dist, 0, 1) * shadow * 0.6
        
        # Apply soft shadow
        for c in range(3):
            image[:, :, c] = image[:, :, c] * (1.0 - shadow_strength)
        
        # Key squares A and B - BOTH have the exact same value: 0.47
        target = self._target_value
        marker_size = sq  # Full square size for visibility
        
        # Position for square A (in the lit area - should LOOK dark)
        ax, ay = int(width * 0.25), int(height * 0.65)
        
        # Position for square B (in the shadow area - should LOOK light)
        bx, by = int(width * 0.55), int(height * 0.35)
        
        # Draw the key squares with identical values
        image[ay:ay+marker_size, ax:ax+marker_size] = target
        image[by:by+marker_size, bx:bx+marker_size] = target
        
        # Add small letter markers near the squares (as bright spots)
        # Mark A with a small bright dot above
        self._draw_label(image, ax + marker_size//2, ay - 10, "A")
        self._draw_label(image, bx + marker_size//2, by - 10, "B")
        
        return np.clip(image, 0, 1)
    
    def _draw_label(self, image: np.ndarray, x: int, y: int, label: str):
        """Draw a simple label marker (just a small colored dot for now)."""
        height, width = image.shape[:2]
        radius = 5
        # Draw a small circle
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                if dx*dx + dy*dy <= radius*radius:
                    py, px = y + dy, x + dx
                    if 0 <= py < height and 0 <= px < width:
                        # Yellow marker
                        image[py, px] = [1.0, 0.9, 0.2]
    
    def get_proof_info(self) -> str:
        """Proof that A and B are identical."""
        v = self._target_value
        rgb_8bit = int(v * 255)
        hex_color = ColorManagement.rgb_to_hex(np.array([v, v, v]))
        return (
            f"--- PIXEL PROOF ---\n"
            f"Squares A and B are IDENTICAL:\n"
            f"  Gray Level: {v:.3f}\n"
            f"  RGB 8-bit: ({rgb_8bit}, {rgb_8bit}, {rgb_8bit})\n"
            f"  HEX: {hex_color}\n"
            f"\n"
            f"Yet A appears dark and B appears light!\n"
            f"Sample any pixel to verify."
        )


@dataclass
class CornsweetParams:
    """Parameters for Cornsweet edge illusion.
    
    Research indicates:
    - Wide ramps with low contrast (< 20%) produce strongest illusion
    - The visual system is more sensitive to sharp edges than gradients
    - Lower contrast makes illusion almost indistinguishable from real step
    """
    edge_width: int = 80  # Wider edge for stronger effect
    edge_contrast: float = 0.15  # ~15% contrast works best per research
    base_luminance: float = 0.5


@register_module
class CornsweetModule:
    """
    Cornsweet Edge (Craik-O'Brien-Cornsweet) Illusion.
    
    A luminance edge between two regions of identical luminance
    makes them appear to have different overall brightness.
    
    The narrow gradient 'fools' the visual system into perceiving
    a brightness step that extends across the entire surface.
    """
    
    def __init__(self, params: Optional[CornsweetParams] = None):
        self.params = params or CornsweetParams()
        self.show_edge = True
    
    @property
    def name(self) -> str:
        return "Cornsweet Edge Illusion"
    
    @property
    def description(self) -> str:
        return (
            "Both halves have IDENTICAL luminance, but the narrow edge gradient "
            "makes the left side appear darker than the right. "
            "Toggle 'Mask Edge' to see they're the same."
        )
    
    @property
    def has_safety_warning(self) -> bool:
        return False
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render the Cornsweet illusion."""
        image = np.full((height, width, 3), self.params.base_luminance, dtype=np.float32)
        
        if self.show_edge:
            center = width // 2
            edge_half = self.params.edge_width // 2
            
            for x in range(width):
                if center - edge_half <= x <= center:
                    # Left side of edge - ramp up
                    t = (x - (center - edge_half)) / edge_half
                    adjustment = self.params.edge_contrast * (1 - t)
                    image[:, x] -= adjustment
                elif center < x <= center + edge_half:
                    # Right side of edge - ramp down
                    t = (x - center) / edge_half
                    adjustment = self.params.edge_contrast * (1 - t)
                    image[:, x] += adjustment
        
        return np.clip(image, 0, 1)
    
    def toggle_edge(self):
        """Toggle edge visibility to prove regions are identical."""
        self.show_edge = not self.show_edge
    
    def get_proof_info(self) -> str:
        """Proof about the regions."""
        l = self.params.base_luminance
        hex_color = ColorManagement.rgb_to_hex(np.array([l, l, l]))
        return (
            f"--- PIXEL PROOF ---\n"
            f"Left and right regions are IDENTICAL:\n"
            f"  Luminance: {l:.3f}\n"
            f"  HEX: {hex_color}\n"
            f"\n"
            f"Only the NARROW EDGE differs.\n"
            f"Mask the edge to see they're the same!"
        )


@register_module
class NeonSpreadingModule:
    """
    Neon Color Spreading / Van Tuijl Illusion.
    
    Based on research: Uses Ehrenstein figure with colored inducers.
    Red/blue colors work best for the neon spreading effect.
    The colored segments near the center create an illusory glow.
    """
    
    def __init__(self):
        # Blue works very well for neon spreading (per research)
        self.inducer_color = (0.2, 0.4, 1.0)  # Bright blue
        self.line_width = 4
        self.num_lines = 16  # Number of radial lines
        self.show_inducers = True
        self.inner_radius = 60  # Where colored segment ends
        self.outer_radius = 200  # Full line length
    
    @property
    def name(self) -> str:
        return "Neon Color Spreading"
    
    @property
    def description(self) -> str:
        return (
            "Ehrenstein neon spreading illusion: Blue line segments at the center "
            "cause an illusory blue glow to spread into the white area. "
            "The interior is physically WHITE - the blue tint is an illusion!"
        )
    
    @property
    def has_safety_warning(self) -> bool:
        return False
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render the neon spreading illusion with Ehrenstein pattern - VECTORIZED."""
        # Slightly off-white background (helps the illusion)
        image = np.full((height, width, 3), 0.95, dtype=np.float32)
        
        cx, cy = width // 2, height // 2
        
        # Create coordinate grids
        y_coords, x_coords = np.ogrid[:height, :width]
        dx = x_coords - cx
        dy = y_coords - cy
        
        # Calculate polar coordinates
        dist = np.sqrt(dx * dx + dy * dy)
        angle = np.arctan2(dy, dx)
        
        # Angular width of each line (approximate constant for simplicity)
        angular_spacing = 2 * np.pi / self.num_lines
        line_half_width = angular_spacing * 0.15  # ~30% of spacing = line width
        
        # Quantize angles to nearest line
        # This is much faster than looping through each line
        angle_mod = (angle + np.pi) % (2 * np.pi)  # Shift to [0, 2pi]
        nearest_line_angle = np.round(angle_mod / angular_spacing) * angular_spacing
        angle_diff = np.abs(angle_mod - nearest_line_angle)
        
        # Mask for being on any radial line
        on_line = (angle_diff < line_half_width) & (dist <= self.outer_radius) & (dist > 5)
        
        # Inner vs outer segments
        inner = on_line & (dist < self.inner_radius)
        outer = on_line & (dist >= self.inner_radius)
        
        # Apply colors
        if self.show_inducers:
            image[inner] = self.inducer_color
        else:
            image[inner] = (0, 0, 0)
        
        image[outer] = (0, 0, 0)
        
        return image
    
    def toggle_inducers(self):
        """Toggle inducer visibility to prove there's no actual spreading."""
        self.show_inducers = not self.show_inducers
    
    def get_proof_info(self) -> str:
        """Proof about the spreading region."""
        return (
            f"--- PIXEL PROOF ---\n"
            f"The center region between the lines is PURE WHITE:\n"
            f"  RGB: (242, 242, 242) - 95% white\n"
            f"  HEX: #F2F2F2\n"
            f"\n"
            f"The blue 'glow' effect spreading into\n"
            f"the white area is an ILLUSION created\n"
            f"by the colored line segments!\n"
            f"\n"
            f"(Blue works best per Van Tuijl research)"
        )


# Test when run directly
if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    modules = [
        SimultaneousContrastModule(),
        CheckerShadowModule(),
        CornsweetModule(),
        NeonSpreadingModule()
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for ax, module in zip(axes, modules):
        image = module.render(400, 300)
        ax.imshow(image)
        ax.set_title(module.name)
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('contrast_illusions_test.png', dpi=150)
    print("Saved test image to contrast_illusions_test.png")
    
    for module in modules:
        print(f"\n{module.name}")
        print("=" * 40)
        print(module.get_proof_info())
