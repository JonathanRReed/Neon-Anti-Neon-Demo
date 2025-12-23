"""
Validation Tools for Color Perception Laboratory
Provides eyedropper, pixel proof modes, and verification utilities.

These tools allow users to verify that color patches are truly identical
in different contexts, proving that perceptual differences are illusions.
"""

import numpy as np
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

# Import our color management
from color_management import ColorManagement, srgb_to_linear, linear_to_srgb


@dataclass
class PixelInfo:
    """Complete information about a pixel's color values."""
    x: int
    y: int
    srgb: Tuple[float, float, float]
    linear: Tuple[float, float, float]
    hex_color: str
    luminance: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/export."""
        return {
            'x': self.x,
            'y': self.y,
            'srgb_r': self.srgb[0],
            'srgb_g': self.srgb[1],
            'srgb_b': self.srgb[2],
            'linear_r': self.linear[0],
            'linear_g': self.linear[1],
            'linear_b': self.linear[2],
            'hex': self.hex_color,
            'luminance': self.luminance
        }


class EyedropperTool:
    """
    Interactive eyedropper tool for inspecting pixel values.
    
    Click any pixel to see its sRGB, linear RGB, hex, and luminance values.
    """
    
    def __init__(self, image_buffer: Optional[np.ndarray] = None):
        """
        Initialize eyedropper with optional image buffer.
        
        Args:
            image_buffer: The image to sample from (H, W, 3 or 4)
        """
        self.image_buffer = image_buffer
        self.sample_history: List[PixelInfo] = []
        self.max_history = 100
    
    def set_image(self, image_buffer: np.ndarray) -> None:
        """Update the image buffer to sample from."""
        self.image_buffer = image_buffer
    
    def sample_pixel(self, x: int, y: int) -> Optional[PixelInfo]:
        """
        Sample a pixel and return its color information.
        
        Args:
            x: X coordinate (column)
            y: Y coordinate (row)
            
        Returns:
            PixelInfo with complete color information, or None if invalid
        """
        if self.image_buffer is None:
            return None
        
        # Bounds check
        h, w = self.image_buffer.shape[:2]
        if x < 0 or x >= w or y < 0 or y >= h:
            return None
        
        # Get sRGB values
        pixel = self.image_buffer[y, x]
        if len(pixel) >= 3:
            srgb = (float(pixel[0]), float(pixel[1]), float(pixel[2]))
        else:
            return None
        
        # Convert to linear
        linear_arr = srgb_to_linear(np.array(srgb))
        linear = (float(linear_arr[0]), float(linear_arr[1]), float(linear_arr[2]))
        
        # Compute hex
        hex_color = ColorManagement.rgb_to_hex(np.array(srgb))
        
        # Compute luminance
        luminance = float(ColorManagement.compute_luminance(np.array(srgb), 'srgb'))
        
        # Create info object
        info = PixelInfo(
            x=x,
            y=y,
            srgb=srgb,
            linear=linear,
            hex_color=hex_color,
            luminance=luminance
        )
        
        # Add to history
        self.sample_history.append(info)
        if len(self.sample_history) > self.max_history:
            self.sample_history.pop(0)
        
        return info
    
    def format_info(self, info: PixelInfo) -> str:
        """
        Format pixel info for display.
        
        Args:
            info: PixelInfo to format
            
        Returns:
            Formatted string for UI display
        """
        return (
            f"Position: ({info.x}, {info.y})\n"
            f"sRGB: ({info.srgb[0]:.3f}, {info.srgb[1]:.3f}, {info.srgb[2]:.3f})\n"
            f"sRGB 8-bit: ({int(info.srgb[0]*255)}, {int(info.srgb[1]*255)}, {int(info.srgb[2]*255)})\n"
            f"Linear: ({info.linear[0]:.4f}, {info.linear[1]:.4f}, {info.linear[2]:.4f})\n"
            f"HEX: {info.hex_color}\n"
            f"Luminance: {info.luminance:.4f}"
        )
    
    def clear_history(self) -> None:
        """Clear the sample history."""
        self.sample_history.clear()


class PixelProofOverlay:
    """
    Generate proof overlays showing that patches have identical RGB.
    
    This is critical for illusion demonstrations - users can verify
    that the center patches are truly the same color.
    """
    
    @staticmethod
    def compare_regions(
        image: np.ndarray,
        region1: Tuple[int, int, int, int],  # x, y, w, h
        region2: Tuple[int, int, int, int]
    ) -> Dict:
        """
        Compare two regions and report if they're pixel-identical.
        
        Args:
            image: Image array (H, W, 3 or 4)
            region1: First region (x, y, width, height)
            region2: Second region (x, y, width, height)
            
        Returns:
            Dictionary with comparison results
        """
        x1, y1, w1, h1 = region1
        x2, y2, w2, h2 = region2
        
        # Extract regions
        patch1 = image[y1:y1+h1, x1:x1+w1, :3]
        patch2 = image[y2:y2+h2, x2:x2+w2, :3]
        
        # Check if same size
        if patch1.shape != patch2.shape:
            return {
                'identical': False,
                'reason': 'Different sizes',
                'patch1_shape': patch1.shape,
                'patch2_shape': patch2.shape
            }
        
        # Check if identical
        max_diff = np.max(np.abs(patch1.astype(float) - patch2.astype(float)))
        mean_diff = np.mean(np.abs(patch1.astype(float) - patch2.astype(float)))
        
        # Compute mean colors
        mean1 = np.mean(patch1, axis=(0, 1))
        mean2 = np.mean(patch2, axis=(0, 1))
        
        return {
            'identical': max_diff < 1e-6,
            'max_difference': float(max_diff),
            'mean_difference': float(mean_diff),
            'patch1_mean_rgb': tuple(float(v) for v in mean1),
            'patch2_mean_rgb': tuple(float(v) for v in mean2),
            'patch1_hex': ColorManagement.rgb_to_hex(mean1),
            'patch2_hex': ColorManagement.rgb_to_hex(mean2)
        }
    
    @staticmethod
    def create_proof_text(
        patch_rgb: Tuple[float, float, float],
        label: str = "Center Patch"
    ) -> str:
        """
        Create text for proof overlay.
        
        Args:
            patch_rgb: RGB values of the patch (0-1 range)
            label: Label for the patch
            
        Returns:
            Formatted proof text
        """
        hex_color = ColorManagement.rgb_to_hex(np.array(patch_rgb))
        rgb_8bit = (int(patch_rgb[0]*255), int(patch_rgb[1]*255), int(patch_rgb[2]*255))
        
        return f"{label} RGB: {hex_color} = ({rgb_8bit[0]}, {rgb_8bit[1]}, {rgb_8bit[2]})"
    
    @staticmethod
    def generate_uniformity_check(
        patch: np.ndarray,
        tolerance: float = 0.001
    ) -> Dict:
        """
        Check if a patch is uniform (all pixels same color).
        
        Args:
            patch: Patch array (H, W, 3)
            tolerance: Maximum allowed variation
            
        Returns:
            Uniformity check results
        """
        if patch.size == 0:
            return {'uniform': False, 'reason': 'Empty patch'}
        
        mean_color = np.mean(patch, axis=(0, 1))
        max_deviation = np.max(np.abs(patch - mean_color))
        
        return {
            'uniform': max_deviation < tolerance,
            'mean_color': tuple(float(v) for v in mean_color),
            'max_deviation': float(max_deviation),
            'hex': ColorManagement.rgb_to_hex(mean_color)
        }


class VerificationReport:
    """
    Generate verification reports for pixel-level validation.
    """
    
    def __init__(self):
        self.entries: List[Dict] = []
        self.created = datetime.now()
    
    def add_comparison(
        self,
        name: str,
        region1_info: Dict,
        region2_info: Dict,
        identical: bool
    ) -> None:
        """Add a comparison entry to the report."""
        self.entries.append({
            'type': 'comparison',
            'name': name,
            'region1': region1_info,
            'region2': region2_info,
            'identical': identical,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_sample(self, name: str, pixel_info: PixelInfo) -> None:
        """Add a pixel sample to the report."""
        self.entries.append({
            'type': 'sample',
            'name': name,
            'pixel': pixel_info.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
    
    def export_text(self) -> str:
        """Export report as formatted text."""
        lines = [
            "=" * 60,
            "COLOR PERCEPTION LABORATORY - VERIFICATION REPORT",
            f"Generated: {self.created.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            ""
        ]
        
        for i, entry in enumerate(self.entries, 1):
            lines.append(f"Entry {i}: {entry['name']}")
            lines.append("-" * 40)
            
            if entry['type'] == 'comparison':
                lines.append(f"  Identical: {'YES ✓' if entry['identical'] else 'NO ✗'}")
                lines.append(f"  Region 1: {entry['region1']}")
                lines.append(f"  Region 2: {entry['region2']}")
            elif entry['type'] == 'sample':
                p = entry['pixel']
                lines.append(f"  Position: ({p['x']}, {p['y']})")
                lines.append(f"  sRGB: ({p['srgb_r']:.4f}, {p['srgb_g']:.4f}, {p['srgb_b']:.4f})")
                lines.append(f"  HEX: {p['hex']}")
                lines.append(f"  Luminance: {p['luminance']:.4f}")
            
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("END OF REPORT")
        
        return "\n".join(lines)
    
    def export_csv(self) -> str:
        """Export report as CSV for analysis."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'entry_num', 'type', 'name', 'timestamp',
            'x', 'y', 'srgb_r', 'srgb_g', 'srgb_b',
            'hex', 'luminance', 'identical'
        ])
        
        for i, entry in enumerate(self.entries, 1):
            if entry['type'] == 'sample':
                p = entry['pixel']
                writer.writerow([
                    i, 'sample', entry['name'], entry['timestamp'],
                    p['x'], p['y'], p['srgb_r'], p['srgb_g'], p['srgb_b'],
                    p['hex'], p['luminance'], ''
                ])
            elif entry['type'] == 'comparison':
                writer.writerow([
                    i, 'comparison', entry['name'], entry['timestamp'],
                    '', '', '', '', '',
                    '', '', entry['identical']
                ])
        
        return output.getvalue()


class CalibrationChecker:
    """
    Tools to help users calibrate their display for accurate perception.
    """
    
    @staticmethod
    def get_calibration_instructions() -> List[str]:
        """Get list of calibration instructions."""
        return [
            "For accurate color perception experiments:",
            "",
            "1. DISABLE display enhancements:",
            "   • Night Shift / Night Light / f.lux",
            "   • True Tone (if available)",
            "   • HDR / HDR tone mapping",
            "   • 'Vivid' or color boost modes",
            "",
            "2. SET display brightness to ~70%",
            "   (Not too bright, not too dim)",
            "",
            "3. USE full-screen mode if possible",
            "   (Minimizes UI distractions)",
            "",
            "4. DIM room lights or use dark environment",
            "   (Reduces screen reflections)",
            "",
            "5. WAIT 2-3 minutes for eye adaptation",
            "   (Before judging subtle colors)",
            "",
            "Note: Different displays will show colors",
            "differently. This app demonstrates perception,",
            "not device-independent 'true' color."
        ]
    
    @staticmethod
    def generate_gray_ramp(width: int, height: int) -> np.ndarray:
        """
        Generate a gray ramp for display calibration.
        
        The ramp should show smooth gradation if gamma is correct.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            Gray ramp image (H, W, 3)
        """
        # Create horizontal gradient
        x = np.linspace(0, 1, width)
        ramp = np.tile(x, (height, 1))
        
        # Stack to RGB
        return np.stack([ramp, ramp, ramp], axis=-1).astype(np.float32)
    
    @staticmethod  
    def generate_gamma_test_pattern(size: int = 200) -> np.ndarray:
        """
        Generate a gamma test pattern.
        
        The striped region should match the uniform region at correct gamma.
        
        Args:
            size: Pattern size (square)
            
        Returns:
            Test pattern image (size, size*2, 3)
        """
        # Left side: 50% gray
        left = np.full((size, size, 3), 0.5, dtype=np.float32)
        
        # Right side: alternating black and white stripes
        right = np.zeros((size, size, 3), dtype=np.float32)
        for i in range(size):
            if (i // 2) % 2 == 0:
                right[:, i, :] = 1.0  # White stripe
            # else: stays black
        
        # Combine
        pattern = np.concatenate([left, right], axis=1)
        
        return pattern
