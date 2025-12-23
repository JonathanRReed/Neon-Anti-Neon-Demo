#!/usr/bin/env python3
"""
Tests for the Color Management module.
Validates sRGB/linear conversions and color operations.
"""

import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from color_management import (
    ColorManagement, ColorAppearance,
    srgb_to_linear, linear_to_srgb, blend_colors
)


def test_srgb_linear_roundtrip():
    """Test that sRGB -> linear -> sRGB roundtrip preserves values."""
    print("Testing sRGB/linear roundtrip...")
    
    test_values = [0.0, 0.04, 0.1, 0.5, 0.8, 1.0]
    
    for val in test_values:
        original = np.array([val, val, val])
        linear = srgb_to_linear(original)
        back = linear_to_srgb(linear)
        
        # Should match within floating point tolerance
        diff = np.max(np.abs(original - back))
        assert diff < 1e-5, f"Roundtrip failed for {val}: diff = {diff}"
    
    print("✓ sRGB/linear roundtrip test passed")


def test_srgb_to_linear_known_values():
    """Test sRGB to linear conversion with known values."""
    print("Testing sRGB to linear with known values...")
    
    # Black should stay black
    black_linear = srgb_to_linear(np.array([0.0, 0.0, 0.0]))
    assert np.allclose(black_linear, [0.0, 0.0, 0.0]), "Black conversion failed"
    
    # White should stay white
    white_linear = srgb_to_linear(np.array([1.0, 1.0, 1.0]))
    assert np.allclose(white_linear, [1.0, 1.0, 1.0]), "White conversion failed"
    
    # 50% gray in sRGB should be ~21.4% in linear (due to gamma)
    gray_linear = srgb_to_linear(np.array([0.5, 0.5, 0.5]))
    assert 0.2 < gray_linear[0] < 0.25, f"Gray conversion incorrect: {gray_linear[0]}"
    
    print("✓ sRGB to linear known values test passed")


def test_linear_blend():
    """Test that linear blending works correctly."""
    print("Testing linear color blending...")
    
    # Blending white and black should give 50% luminance, not 50% sRGB value
    white = np.array([1.0, 1.0, 1.0])
    black = np.array([0.0, 0.0, 0.0])
    
    blended = blend_colors([white, black], [0.5, 0.5])
    
    # Result should be the sRGB encoding of 50% linear light
    # 50% linear ≈ 73.5% sRGB (due to gamma)
    expected_srgb = linear_to_srgb(np.array([0.5, 0.5, 0.5]))
    
    diff = np.max(np.abs(blended - expected_srgb))
    assert diff < 1e-5, f"Blend result incorrect: {blended} vs expected {expected_srgb}"
    
    print("✓ Linear color blending test passed")


def test_luminance_calculation():
    """Test luminance calculation."""
    print("Testing luminance calculation...")
    
    # White should have luminance 1.0
    white_lum = ColorManagement.compute_luminance(np.array([1.0, 1.0, 1.0]), 'srgb')
    assert abs(white_lum - 1.0) < 0.01, f"White luminance incorrect: {white_lum}"
    
    # Black should have luminance 0.0
    black_lum = ColorManagement.compute_luminance(np.array([0.0, 0.0, 0.0]), 'srgb')
    assert abs(black_lum) < 0.01, f"Black luminance incorrect: {black_lum}"
    
    # Pure green should have higher luminance than pure red or blue
    # (due to ITU-R BT.709 coefficients)
    red_lum = ColorManagement.compute_luminance(np.array([1.0, 0.0, 0.0]), 'srgb')
    green_lum = ColorManagement.compute_luminance(np.array([0.0, 1.0, 0.0]), 'srgb')
    blue_lum = ColorManagement.compute_luminance(np.array([0.0, 0.0, 1.0]), 'srgb')
    
    assert green_lum > red_lum, "Green should be more luminous than red"
    assert green_lum > blue_lum, "Green should be more luminous than blue"
    
    print("✓ Luminance calculation test passed")


def test_hex_conversion():
    """Test RGB to hex and back."""
    print("Testing hex conversion...")
    
    # Test known conversions
    test_cases = [
        ([1.0, 0.0, 0.0], "#FF0000"),
        ([0.0, 1.0, 0.0], "#00FF00"),
        ([0.0, 0.0, 1.0], "#0000FF"),
        ([1.0, 1.0, 1.0], "#FFFFFF"),
        ([0.0, 0.0, 0.0], "#000000"),
    ]
    
    for rgb, expected_hex in test_cases:
        result = ColorManagement.rgb_to_hex(np.array(rgb))
        assert result == expected_hex, f"RGB {rgb} -> {result}, expected {expected_hex}"
        
        # Test reverse
        back = ColorManagement.hex_to_rgb(expected_hex)
        assert np.allclose(back, rgb, atol=1/256), f"Hex {expected_hex} -> {back}, expected {rgb}"
    
    print("✓ Hex conversion test passed")


def test_brown_probability():
    """Test brown probability prediction."""
    print("Testing brown probability prediction...")
    
    # Orange hue with low luminance on bright surround should have high P(brown)
    p_brown_high = ColorAppearance.predict_brown_probability(
        hue=30,  # Orange
        saturation=0.7,
        luminance=0.35,
        surround_luminance=0.9  # Bright surround
    )
    
    # Same color on dim surround should have lower P(brown)
    p_brown_low = ColorAppearance.predict_brown_probability(
        hue=30,
        saturation=0.7,
        luminance=0.35,
        surround_luminance=0.1  # Dim surround
    )
    
    assert p_brown_high > p_brown_low, (
        f"Bright surround should increase P(brown): "
        f"bright={p_brown_high:.3f}, dim={p_brown_low:.3f}"
    )
    
    # Blue hue should have low P(brown) regardless of surround
    p_brown_blue = ColorAppearance.predict_brown_probability(
        hue=240,  # Blue
        saturation=0.7,
        luminance=0.35,
        surround_luminance=0.9
    )
    
    assert p_brown_blue < p_brown_high, "Blue should have lower P(brown) than orange"
    
    print("✓ Brown probability prediction test passed")


def test_clamping():
    """Test that values are properly clamped."""
    print("Testing value clamping...")
    
    # Values outside [0, 1] should be clamped
    out_of_range = np.array([1.5, -0.5, 2.0])
    linear = srgb_to_linear(out_of_range)
    
    assert np.all(linear >= 0.0), "Linear values should be >= 0"
    assert np.all(linear <= 1.0), "Linear values should be <= 1"
    
    srgb = linear_to_srgb(out_of_range)
    assert np.all(srgb >= 0.0), "sRGB values should be >= 0"
    assert np.all(srgb <= 1.0), "sRGB values should be <= 1"
    
    print("✓ Value clamping test passed")


def run_all_tests():
    """Run all color management tests."""
    print("=" * 50)
    print("Running Color Management Tests")
    print("=" * 50)
    
    tests = [
        test_srgb_linear_roundtrip,
        test_srgb_to_linear_known_values,
        test_linear_blend,
        test_luminance_calculation,
        test_hex_conversion,
        test_brown_probability,
        test_clamping,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
