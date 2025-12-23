"""
Color Management Module for Color Perception Laboratory
Handles sRGB/linear color space conversions and physically-correct color operations.

This module ensures all color blending, blur, and glow operations happen in
linear light space (not gamma-encoded sRGB) for physical correctness.
"""

import numpy as np
from typing import Tuple, List, Union, Optional

# Constants for sRGB conversion
SRGB_GAMMA = 2.4
SRGB_LINEAR_THRESHOLD = 0.04045
SRGB_LINEAR_SCALE = 12.92
SRGB_NONLINEAR_OFFSET = 0.055
SRGB_NONLINEAR_SCALE = 1.055


class ColorManagement:
    """
    sRGB-correct color management with linear-light operations.
    
    All internal operations (blending, blur, bloom) should be done in linear
    light space. Convert to/from sRGB only at input/output boundaries.
    """
    
    @staticmethod
    def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
        """
        Convert sRGB gamma-encoded values to linear light.
        
        Uses the proper piecewise sRGB transfer function:
        - For values <= 0.04045: linear = srgb / 12.92
        - For values > 0.04045: linear = ((srgb + 0.055) / 1.055) ^ 2.4
        
        Args:
            srgb: Array of sRGB values in range [0, 1]
            
        Returns:
            Array of linear light values in range [0, 1]
        """
        srgb = np.asarray(srgb, dtype=np.float64)
        srgb = np.clip(srgb, 0.0, 1.0)
        
        # Piecewise conversion
        linear = np.where(
            srgb <= SRGB_LINEAR_THRESHOLD,
            srgb / SRGB_LINEAR_SCALE,
            np.power((srgb + SRGB_NONLINEAR_OFFSET) / SRGB_NONLINEAR_SCALE, SRGB_GAMMA)
        )
        
        return linear.astype(np.float32)
    
    @staticmethod
    def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
        """
        Convert linear light values to sRGB gamma-encoded.
        
        Uses the inverse piecewise sRGB transfer function:
        - For values <= 0.0031308: srgb = linear * 12.92
        - For values > 0.0031308: srgb = 1.055 * linear^(1/2.4) - 0.055
        
        Args:
            linear: Array of linear light values in range [0, 1]
            
        Returns:
            Array of sRGB gamma-encoded values in range [0, 1]
        """
        linear = np.asarray(linear, dtype=np.float64)
        linear = np.clip(linear, 0.0, 1.0)
        
        # Inverse threshold for linear -> sRGB
        linear_threshold = SRGB_LINEAR_THRESHOLD / SRGB_LINEAR_SCALE  # ~0.0031308
        
        srgb = np.where(
            linear <= linear_threshold,
            linear * SRGB_LINEAR_SCALE,
            SRGB_NONLINEAR_SCALE * np.power(linear, 1.0 / SRGB_GAMMA) - SRGB_NONLINEAR_OFFSET
        )
        
        return np.clip(srgb, 0.0, 1.0).astype(np.float32)
    
    @staticmethod
    def blend_linear(colors: List[np.ndarray], weights: List[float]) -> np.ndarray:
        """
        Blend multiple colors in linear light space (physically correct).
        
        This is how light actually mixes - additive in linear space.
        Do NOT blend in gamma-encoded sRGB space!
        
        Args:
            colors: List of sRGB color arrays (each RGB or RGBA)
            weights: List of blend weights (will be normalized)
            
        Returns:
            Blended color in sRGB space
        """
        if len(colors) != len(weights):
            raise ValueError("Colors and weights must have same length")
        
        if len(colors) == 0:
            raise ValueError("At least one color required")
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            raise ValueError("Weights cannot sum to zero")
        normalized_weights = [w / total_weight for w in weights]
        
        # Convert all to linear
        linear_colors = [ColorManagement.srgb_to_linear(c) for c in colors]
        
        # Weighted sum in linear space
        result = np.zeros_like(linear_colors[0], dtype=np.float64)
        for color, weight in zip(linear_colors, normalized_weights):
            result += color * weight
        
        # Convert back to sRGB
        return ColorManagement.linear_to_srgb(result)
    
    @staticmethod
    def apply_bloom_linear(
        image: np.ndarray,
        intensity: float = 0.5,
        radius: int = 10
    ) -> np.ndarray:
        """
        Apply bloom/glow effect in linear light space.
        
        Bloom should be computed in linear space for physical correctness.
        This avoids the "muddy" look of gamma-space blur.
        
        Args:
            image: sRGB image array (H, W, 3 or 4)
            intensity: Bloom intensity (0-1)
            radius: Blur radius in pixels
            
        Returns:
            sRGB image with bloom applied
        """
        from scipy.ndimage import gaussian_filter
        
        image = np.asarray(image, dtype=np.float32)
        has_alpha = image.shape[-1] == 4
        
        # Separate RGB and alpha
        if has_alpha:
            rgb = image[..., :3]
            alpha = image[..., 3:4]
        else:
            rgb = image
        
        # Convert to linear
        linear = ColorManagement.srgb_to_linear(rgb)
        
        # Apply gaussian blur in linear space
        blurred = np.zeros_like(linear)
        for c in range(3):
            blurred[..., c] = gaussian_filter(linear[..., c], sigma=radius)
        
        # Blend original with bloom
        result_linear = linear + blurred * intensity
        result_linear = np.clip(result_linear, 0.0, 1.0)
        
        # Convert back to sRGB
        result = ColorManagement.linear_to_srgb(result_linear)
        
        if has_alpha:
            result = np.concatenate([result, alpha], axis=-1)
        
        return result
    
    @staticmethod
    def compute_luminance(rgb: np.ndarray, space: str = 'srgb') -> np.ndarray:
        """
        Compute relative luminance from RGB.
        
        Args:
            rgb: RGB array (sRGB or linear depending on space param)
            space: 'srgb' or 'linear'
            
        Returns:
            Luminance array
        """
        if space == 'srgb':
            linear = ColorManagement.srgb_to_linear(rgb)
        else:
            linear = np.asarray(rgb)
        
        # ITU-R BT.709 luminance coefficients
        return 0.2126 * linear[..., 0] + 0.7152 * linear[..., 1] + 0.0722 * linear[..., 2]
    
    @staticmethod
    def adjust_luminance(rgb: np.ndarray, target_luminance: float) -> np.ndarray:
        """
        Adjust RGB to have specific luminance while preserving hue.
        
        Args:
            rgb: sRGB color array
            target_luminance: Target relative luminance (0-1)
            
        Returns:
            Adjusted sRGB color
        """
        linear = ColorManagement.srgb_to_linear(rgb)
        current_lum = ColorManagement.compute_luminance(rgb, space='linear')
        
        if current_lum < 1e-10:
            # Handle near-black by setting to gray
            return ColorManagement.linear_to_srgb(
                np.full_like(linear, target_luminance)
            )
        
        # Scale to target luminance
        scale = target_luminance / current_lum
        adjusted = linear * scale
        adjusted = np.clip(adjusted, 0.0, 1.0)
        
        return ColorManagement.linear_to_srgb(adjusted)
    
    @staticmethod
    def rgb_to_hex(rgb: np.ndarray) -> str:
        """
        Convert RGB (0-1 range) to hex string.
        
        Args:
            rgb: RGB array with values in [0, 1]
            
        Returns:
            Hex string like '#FF00FF'
        """
        rgb = np.clip(np.asarray(rgb), 0.0, 1.0)
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        return f"#{r:02X}{g:02X}{b:02X}"
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> np.ndarray:
        """
        Convert hex string to RGB (0-1 range).
        
        Args:
            hex_color: Hex string like '#FF00FF' or 'FF00FF'
            
        Returns:
            RGB array with values in [0, 1]
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color: {hex_color}")
        
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        return np.array([r, g, b], dtype=np.float32)


class ColorAppearance:
    """
    Simplified color appearance calculations for demonstration.
    
    This provides basic CAM-like computations without implementing
    the full CIECAM02/16 model. Useful for showing how surround
    affects perceived attributes.
    """
    
    @staticmethod
    def estimate_perceived_lightness(
        luminance: float,
        surround_luminance: float,
        adaptation_factor: float = 0.5
    ) -> float:
        """
        Estimate perceived lightness based on surround.
        
        Higher surround luminance makes the target appear darker.
        This is a simplified model of the simultaneous contrast effect.
        
        Args:
            luminance: Target luminance (0-1)
            surround_luminance: Surround luminance (0-1)
            adaptation_factor: How much surround affects perception (0-1)
            
        Returns:
            Estimated perceived lightness (0-1)
        """
        # Adaptation shifts the perception
        # High surround makes target look darker (contrast effect)
        adaptation_level = surround_luminance * adaptation_factor
        
        # Apply von Kries-like adaptation
        adapted = luminance / (luminance + adaptation_level + 0.1)
        
        # Nonlinear response (approximate L* curve)
        if adapted > 0.008856:
            perceived = 1.16 * np.power(adapted, 1/3) - 0.16
        else:
            perceived = 9.033 * adapted
        
        return np.clip(perceived, 0.0, 1.0)
    
    @staticmethod
    def predict_brown_probability(
        hue: float,
        saturation: float,
        luminance: float,
        surround_luminance: float
    ) -> float:
        """
        Predict probability that a color will be perceived as "brown".
        
        Brown perception depends heavily on:
        1. Hue near orange/yellow-orange (15-45°)
        2. Moderate saturation
        3. Lower perceived lightness (often due to bright surround)
        
        Args:
            hue: Hue in degrees (0-360)
            saturation: Color saturation (0-1)
            luminance: Target luminance (0-1)
            surround_luminance: Surround luminance (0-1)
            
        Returns:
            Estimated P(brown) from 0 to 1
        """
        # Hue factor: peak around 30° (orange), falls off outside 10-50°
        hue_norm = hue % 360
        if 10 <= hue_norm <= 50:
            hue_factor = 1.0 - abs(hue_norm - 30) / 20
        else:
            hue_factor = 0.2  # Low probability outside orange range
        
        # Saturation factor: moderate saturation favors brown
        if 0.3 <= saturation <= 0.8:
            sat_factor = 1.0
        else:
            sat_factor = 0.5
        
        # Key insight: brown perception depends on CONTRAST with surround
        # When surround is brighter than target, the color shifts toward brown
        # The larger the contrast, the stronger the brown perception
        
        contrast_ratio = surround_luminance - luminance
        
        # Brown is perceived when:
        # 1. Target is darker than surround (positive contrast)
        # 2. Target has moderate-low luminance
        
        if contrast_ratio > 0 and luminance < 0.5:
            # Higher contrast = more brown appearance
            # Also consider that very low luminance helps brown perception
            contrast_factor = min(1.0, contrast_ratio / 0.5)  # Normalize contrast
            luminance_factor = 1.0 - luminance  # Lower luminance = more brown potential
            lightness_factor = contrast_factor * luminance_factor
        else:
            # If target is brighter than surround, or very bright target, less likely brown
            lightness_factor = max(0.0, 0.3 - luminance) if luminance < 0.3 else 0.0
        
        # Combine factors
        p_brown = hue_factor * sat_factor * lightness_factor
        
        return float(np.clip(p_brown, 0.0, 1.0))


# Convenience functions for common operations
def srgb_to_linear(srgb):
    """Convenience wrapper for sRGB to linear conversion."""
    return ColorManagement.srgb_to_linear(srgb)


def linear_to_srgb(linear):
    """Convenience wrapper for linear to sRGB conversion."""
    return ColorManagement.linear_to_srgb(linear)


def blend_colors(colors, weights):
    """Convenience wrapper for linear-space color blending."""
    return ColorManagement.blend_linear(colors, weights)
