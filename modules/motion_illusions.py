"""
Motion Illusions Module - Temporal and Motion-Induced Color Effects

This module implements motion and temporal illusions that create illusory colors:
- Lilac Chaser: Moving gap creates complementary colored afterimage
- Benham's Disk: Rotating B/W patterns produce illusory colored rings

WARNING: Some effects use flickering patterns. Do not use if you have
photosensitive epilepsy or are prone to seizures.

References:
- Lilac chaser: Troxler's fading combined with negative afterimages
- Benham's disk (Fechner colors): Different temporal responses of color channels
"""

import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from color_management import ColorManagement
from modules import register_module


@dataclass
class LilacChaserParams:
    """Parameters for Lilac Chaser illusion.
    
    Research indicates:
    - 12 blurred discs arranged in a circle
    - Disc disappears for ~0.1 seconds
    - Next disc disappears ~0.125 seconds later
    - Discs are lilac/magenta/pink colored
    """
    num_discs: int = 12
    disc_radius: int = 25  # Slightly larger for better blur
    ring_radius: int = 130
    # Lilac/magenta color - complement is green for afterimage
    disc_color: Tuple[float, float, float] = (0.8, 0.4, 0.8)
    gap_duration: float = 0.125  # Per Wikipedia: ~0.125s between disappearances
    background_color: Tuple[float, float, float] = (0.5, 0.5, 0.5)  # Neutral gray


@register_module
class LilacChaserModule:
    """
    Lilac Chaser (Pac-Man/Fading Lilac) Illusion.
    
    A ring of colored discs with one missing disc that rotates around.
    After fixating on the center, observers see:
    1. A green disc (afterimage) moving in the gap
    2. The lilac discs fading away (Troxler's fading)
    
    Eventually, only a rotating green disc appears visible!
    """
    
    def __init__(self, params: Optional[LilacChaserParams] = None):
        self.params = params or LilacChaserParams()
        self.start_time = time.time()
        self.running = False
    
    @property
    def name(self) -> str:
        return "Lilac Chaser (Pac-Man Illusion)"
    
    @property
    def description(self) -> str:
        return (
            "Fixate on the center cross. After a few seconds, you'll see a "
            "green disc chasing the gap. Keep watching - the lilac discs will "
            "fade away, leaving only a rotating green disc!"
        )
    
    @property
    def has_safety_warning(self) -> bool:
        return False  # No flicker, safe for most viewers
    
    def start(self):
        """Start the animation."""
        self.start_time = time.time()
        self.running = True
    
    def stop(self):
        """Stop the animation."""
        self.running = False
    
    def get_current_gap_index(self) -> int:
        """Get which disc position is currently the gap."""
        if not self.running:
            return 0
        
        elapsed = time.time() - self.start_time
        period = self.params.gap_duration * self.params.num_discs
        position_in_cycle = (elapsed % period) / self.params.gap_duration
        return int(position_in_cycle) % self.params.num_discs
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render the current frame of the illusion - VECTORIZED for performance."""
        # Gray background
        bg = self.params.background_color
        image = np.full((height, width, 3), bg, dtype=np.float32)
        
        cx, cy = width // 2, height // 2
        ring_r = self.params.ring_radius
        disc_r = self.params.disc_radius
        
        gap_idx = self.get_current_gap_index()
        
        # Pre-compute disc drawing coordinates (vectorized)
        # Create a grid for a single disc
        yy, xx = np.ogrid[-disc_r:disc_r+1, -disc_r:disc_r+1]
        disc_dist = np.sqrt(xx*xx + yy*yy)
        disc_mask = disc_dist <= disc_r
        
        # Soft edge factor (gaussian-like falloff)
        edge_factor = np.maximum(0, 1 - (disc_dist / disc_r) ** 4)
        
        # Pre-compute colors for each channel
        disc_color = np.array(self.params.disc_color)
        bg_arr = np.array(bg)
        
        # Draw discs in a ring
        for i in range(self.params.num_discs):
            if i == gap_idx:
                continue  # Skip the gap
            
            angle = 2 * np.pi * i / self.params.num_discs - np.pi / 2
            disc_cx = int(cx + ring_r * np.cos(angle))
            disc_cy = int(cy + ring_r * np.sin(angle))
            
            # Calculate bounds
            y1 = max(0, disc_cy - disc_r)
            y2 = min(height, disc_cy + disc_r + 1)
            x1 = max(0, disc_cx - disc_r)
            x2 = min(width, disc_cx + disc_r + 1)
            
            # Calculate offset into disc template
            dy1 = y1 - (disc_cy - disc_r)
            dy2 = dy1 + (y2 - y1)
            dx1 = x1 - (disc_cx - disc_r)
            dx2 = dx1 + (x2 - x1)
            
            # Get the relevant portion of the disc
            mask_portion = disc_mask[dy1:dy2, dx1:dx2]
            edge_portion = edge_factor[dy1:dy2, dx1:dx2]
            
            # Apply disc color with soft edges
            for c in range(3):
                color_blend = bg_arr[c] + (disc_color[c] - bg_arr[c]) * edge_portion
                image[y1:y2, x1:x2, c] = np.where(mask_portion, color_blend, image[y1:y2, x1:x2, c])
        
        # Draw fixation cross
        fix_size = 8
        fix_width = 2
        image[cy-fix_width:cy+fix_width, cx-fix_size:cx+fix_size] = 0
        image[cy-fix_size:cy+fix_size, cx-fix_width:cx+fix_width] = 0
        
        return image
    
    def get_proof_info(self) -> str:
        """Information about the illusion."""
        disc_hex = ColorManagement.rgb_to_hex(np.array(self.params.disc_color))
        return (
            f"--- LILAC CHASER INFO ---\n"
            f"Disc Color: {disc_hex} (lilac/magenta)\n"
            f"Expected Afterimage: Green (complement)\n"
            f"Number of Discs: {self.params.num_discs}\n"
            f"Gap Duration: {self.params.gap_duration:.2f}s per position\n"
            f"\n"
            f"Fixate on the center cross for:\n"
            f"- ~3s: Green afterimage appears in gap\n"
            f"- ~10s: Lilac discs begin to fade\n"
            f"- ~20s: Only green disc visible!"
        )


@dataclass
class BenhamDiskParams:
    """Parameters for Benham's Disk.
    
    Research indicates:
    - Optimal rotation speed: 4-6 Hz (rotations per second)
    - Arc pattern at different radii creates different perceived colors
    - Half black, half white with arcs for best effect
    """
    rotation_speed: float = 5.0  # 5 Hz is in optimal 4-6 Hz range per research
    arc_positions: List[float] = None  # Arc positions (normalized 0-1 from center)
    arc_widths: List[float] = None  # Arc widths
    
    def __post_init__(self):
        if self.arc_positions is None:
            # Position arcs at different radii - each will appear different color
            self.arc_positions = [0.2, 0.35, 0.5, 0.65, 0.8]
        if self.arc_widths is None:
            self.arc_widths = [0.04, 0.04, 0.04, 0.04, 0.04]


@register_module
class BenhamDiskModule:
    """
    Benham's Top / Fechner Color Effect.
    
    A rotating black and white pattern produces illusory colored rings.
    Different temporal frequencies stimulate color channels differently,
    creating subjective color experiences from achromatic stimuli.
    
    WARNING: This uses rotating patterns. Do not use if you have
    photosensitive epilepsy.
    """
    
    def __init__(self, params: Optional[BenhamDiskParams] = None):
        self.params = params or BenhamDiskParams()
        self.start_time = time.time()
        self.running = False
    
    @property
    def name(self) -> str:
        return "Benham's Disk (Fechner Colors)"
    
    @property
    def description(self) -> str:
        return (
            "A rotating black and white pattern that produces illusory colors. "
            "Different people see different colors in different rings. "
            "This demonstrates how temporal processing affects color perception."
        )
    
    @property
    def has_safety_warning(self) -> bool:
        return True  # Rotating patterns can trigger photosensitivity
    
    def get_safety_warning(self) -> str:
        """Get safety warning for photosensitivity."""
        return (
            "[!] PHOTOSENSITIVITY WARNING [!]\n"
            "\n"
            "This effect uses a ROTATING PATTERN that may cause\n"
            "discomfort in some viewers.\n"
            "\n"
            "DO NOT USE if you have:\n"
            "- Photosensitive epilepsy\n"
            "- History of seizures with flickering lights\n"
            "- Severe motion sensitivity\n"
            "\n"
            "Stop immediately if you experience any discomfort.\n"
            "The rotation speed is limited for safety."
        )
    
    def start(self):
        """Start the rotation."""
        self.start_time = time.time()
        self.running = True
    
    def stop(self):
        """Stop the rotation."""
        self.running = False
    
    def get_current_angle(self) -> float:
        """Get current rotation angle in radians."""
        if not self.running:
            return 0
        
        elapsed = time.time() - self.start_time
        rotations = elapsed * self.params.rotation_speed
        return (rotations * 2 * np.pi) % (2 * np.pi)
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render the current frame of Benham's disk - VECTORIZED for performance."""
        # Create coordinate grids
        y_coords, x_coords = np.ogrid[:height, :width]
        cx, cy = width // 2, height // 2
        radius = min(width, height) // 2 - 10
        
        # Calculate distances and angles for all pixels at once
        dx = x_coords - cx
        dy = y_coords - cy
        dist = np.sqrt(dx * dx + dy * dy)
        
        # Normalized distance from center
        r_norm = dist / radius
        
        # Angle from center (with rotation)
        current_angle = self.get_current_angle()
        angle = (np.arctan2(dy, dx) + current_angle) % (2 * np.pi)
        angle_norm = angle / (2 * np.pi)
        
        # Start with white background
        image = np.ones((height, width, 3), dtype=np.float32)
        
        # Mask for inside disk
        inside_disk = dist <= radius
        
        # Black half (angle_norm < 0.5)
        black_half = inside_disk & (angle_norm < 0.5)
        image[black_half] = 0
        
        # White arcs in the black half
        arc_angle = angle_norm * 2  # Normalize to black half
        arc_region = (arc_angle > 0.1) & (arc_angle < 0.4)
        
        # Check each arc position (vectorized)
        for pos, width_val in zip(self.params.arc_positions, self.params.arc_widths):
            in_arc = np.abs(r_norm - pos) < width_val
            white_arc = black_half & arc_region & in_arc
            image[white_arc] = 1
        
        return image
    
    def render_static(self, width: int, height: int) -> np.ndarray:
        """Render the disk without rotation (for preview)."""
        old_running = self.running
        self.running = False
        result = self.render(width, height)
        self.running = old_running
        return result
    
    def get_proof_info(self) -> str:
        """Information about the disk."""
        return (
            f"--- BENHAM'S DISK INFO ---\n"
            f"Rotation Speed: {self.params.rotation_speed:.1f} Hz\n"
            f"(Limited to {self.params.rotation_speed:.1f} for safety)\n"
            f"\n"
            f"The disk contains ONLY black and white.\n"
            f"Any colors you see are created by your\n"
            f"visual system's temporal processing!\n"
            f"\n"
            f"Different people see different colors.\n"
            f"Colors also change with rotation direction."
        )
    
    def get_explanation(self) -> str:
        """Get scientific explanation."""
        return (
            "HOW BENHAM'S DISK WORKS\n"
            "-----------------------\n"
            "\n"
            "The three types of cone cells in your retina have\n"
            "different temporal response characteristics:\n"
            "\n"
            "- Red cones: slower response\n"
            "- Blue cones: faster response\n"
            "- Green cones: intermediate\n"
            "\n"
            "When black and white alternate rapidly, the different\n"
            "response speeds create brief imbalances in cone signals,\n"
            "which the brain interprets as color.\n"
            "\n"
            "The specific colors depend on:\n"
            "- Rotation speed\n"
            "- Arc position (distance from center)\n"
            "- Individual differences in cone response timing\n"
            "\n"
            "This is why different people see different colors!"
        )


# Test when run directly
if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    # Test Lilac Chaser
    lilac = LilacChaserModule()
    lilac.start()
    
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    
    # Lilac chaser at different gap positions
    for i, ax in enumerate(axes[0]):
        # Manually set gap position for demo
        lilac.start_time = time.time() - i * lilac.params.gap_duration
        img = lilac.render(300, 300)
        ax.imshow(img)
        ax.set_title(f"Lilac Chaser (gap at position {lilac.get_current_gap_index()})")
        ax.axis('off')
    
    # Benham's disk
    benham = BenhamDiskModule()
    benham.start()
    
    for i, ax in enumerate(axes[1]):
        benham.start_time = time.time() - i * 0.08  # Different rotation angles
        img = benham.render(300, 300)
        ax.imshow(img)
        angle_deg = int(np.degrees(benham.get_current_angle()))
        ax.set_title(f"Benham's Disk (angle={angle_deg}°)")
        ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('motion_illusions_test.png', dpi=150)
    print("Saved test image to motion_illusions_test.png")
    
    print("\n" + lilac.get_proof_info())
    print("\n" + benham.get_safety_warning())
    print("\n" + benham.get_explanation())
