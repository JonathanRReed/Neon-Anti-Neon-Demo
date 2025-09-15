#!/usr/bin/env python3
"""
Basic tests for the Neon & Anti-Neon Demo application.
These tests validate core functionality without requiring a GUI.
"""

import sys
import os
import numpy as np
from typing import Tuple

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from color_engine import ColorEngine


def test_color_engine_initialization():
    """Test that ColorEngine initializes with proper default values"""
    print("Testing ColorEngine initialization...")
    
    engine = ColorEngine()
    
    # Check default values
    assert engine.hue == 0.0, f"Expected hue=0.0, got {engine.hue}"
    assert engine.saturation == 1.0, f"Expected saturation=1.0, got {engine.saturation}"
    assert engine.brightness == 1.0, f"Expected brightness=1.0, got {engine.brightness}"
    assert engine.fluorescence == 0.0, f"Expected fluorescence=0.0, got {engine.fluorescence}"
    assert engine.neon_mode == True, f"Expected neon_mode=True, got {engine.neon_mode}"
    
    print("✓ ColorEngine initialization test passed")


def test_color_value_clamping():
    """Test that color values are properly clamped to valid ranges"""
    print("Testing color value clamping...")
    
    engine = ColorEngine()
    
    # Test hue clamping
    engine.set_hue(-10)  # Should clamp to 0
    assert engine.hue == 0.0, f"Negative hue not clamped, got {engine.hue}"
    
    engine.set_hue(400)  # Should clamp to 360
    assert engine.hue == 360.0, f"High hue not clamped, got {engine.hue}"
    
    # Test saturation clamping
    engine.set_saturation(-0.5)  # Should clamp to 0
    assert engine.saturation == 0.0, f"Negative saturation not clamped, got {engine.saturation}"
    
    engine.set_saturation(1.5)  # Should clamp to 1
    assert engine.saturation == 1.0, f"High saturation not clamped, got {engine.saturation}"
    
    # Test brightness clamping
    engine.set_brightness(-0.1)  # Should clamp to 0
    assert engine.brightness == 0.0, f"Negative brightness not clamped, got {engine.brightness}"
    
    engine.set_brightness(2.0)  # Should clamp to 1
    assert engine.brightness == 1.0, f"High brightness not clamped, got {engine.brightness}"
    
    print("✓ Color value clamping test passed")


def test_hsv_to_rgb_conversion():
    """Test HSV to RGB color conversion"""
    print("Testing HSV to RGB conversion...")
    
    engine = ColorEngine()
    
    # Test pure red (hue=0)
    engine.set_hue(0)
    engine.set_saturation(1.0)
    engine.set_brightness(1.0)
    r, g, b = engine.get_rgb()
    
    # In neon mode, should be bright red-ish
    assert r > 0.5, f"Expected high red component, got {r}"
    assert 0.0 <= r <= 1.0, f"Red component out of range: {r}"
    assert 0.0 <= g <= 1.0, f"Green component out of range: {g}"
    assert 0.0 <= b <= 1.0, f"Blue component out of range: {b}"
    
    # Test pure green (hue=120)
    engine.set_hue(120)
    r, g, b = engine.get_rgb()
    assert g > 0.5, f"Expected high green component, got {g}"
    
    # Test pure blue (hue=240)
    engine.set_hue(240)
    r, g, b = engine.get_rgb()
    assert b > 0.5, f"Expected high blue component, got {b}"
    
    print("✓ HSV to RGB conversion test passed")


def test_neon_vs_anti_neon_modes():
    """Test differences between neon and anti-neon modes"""
    print("Testing neon vs anti-neon modes...")
    
    engine = ColorEngine()
    engine.set_hue(180)  # Cyan
    engine.set_saturation(1.0)
    engine.set_brightness(1.0)
    
    # Test neon mode
    engine.set_neon_mode(True)
    neon_rgb = engine.get_rgb()
    neon_hsv = engine.get_hsv()
    
    # Test anti-neon mode
    engine.set_neon_mode(False)
    anti_neon_rgb = engine.get_rgb()
    anti_neon_hsv = engine.get_hsv()
    
    # Anti-neon should be less saturated and darker
    assert anti_neon_hsv[1] < neon_hsv[1], "Anti-neon should be less saturated"
    assert anti_neon_hsv[2] < neon_hsv[2], "Anti-neon should be darker"
    
    print("✓ Neon vs anti-neon modes test passed")


def test_preset_application():
    """Test preset application functionality"""
    print("Testing preset application...")
    
    engine = ColorEngine()
    
    # Test valid preset
    success = engine.apply_preset("Cool Blue", duration=0.1)
    assert success == True, "Valid preset should return True"
    
    # Test invalid preset
    success = engine.apply_preset("Nonexistent Preset", duration=0.1)
    assert success == False, "Invalid preset should return False"
    
    # Test that preset names are available
    preset_names = ColorEngine.get_preset_names()
    assert len(preset_names) > 0, "Should have preset names available"
    assert "Cool Blue" in preset_names, "Cool Blue preset should be available"
    
    print("✓ Preset application test passed")


def test_input_validation():
    """Test input validation and error handling"""
    print("Testing input validation...")
    
    engine = ColorEngine()
    
    # Test invalid types (should not crash)
    try:
        engine.set_hue("not a number")
        assert False, "Should have raised ValueError for invalid hue type"
    except ValueError:
        pass  # Expected
    except Exception as e:
        assert False, f"Unexpected exception: {e}"
    
    try:
        engine.set_saturation(None)
        assert False, "Should have raised ValueError for None saturation"
    except ValueError:
        pass  # Expected
    except Exception as e:
        assert False, f"Unexpected exception: {e}"
    
    try:
        engine.set_neon_mode("yes")
        assert False, "Should have raised ValueError for invalid neon_mode type"
    except ValueError:
        pass  # Expected
    except Exception as e:
        assert False, f"Unexpected exception: {e}"
    
    print("✓ Input validation test passed")


def test_animation_system():
    """Test animation system functionality"""
    print("Testing animation system...")
    
    engine = ColorEngine()
    
    # Start animation
    engine.animate_to(target_hue=180, target_saturation=0.5, duration=0.1)
    assert engine.is_animating == True, "Animation should be active"
    
    # Update animation (should work without errors)
    original_hue = engine.hue
    engine.update_animation()
    
    # Animation should eventually complete
    import time
    time.sleep(0.15)  # Wait longer than duration
    engine.update_animation()
    assert engine.is_animating == False, "Animation should be complete"
    
    print("✓ Animation system test passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Running Neon & Anti-Neon Demo Tests")
    print("=" * 50)
    
    tests = [
        test_color_engine_initialization,
        test_color_value_clamping,
        test_hsv_to_rgb_conversion,
        test_neon_vs_anti_neon_modes,
        test_preset_application,
        test_input_validation,
        test_animation_system,
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