"""
Color Engine for Neon & Anti-Neon Demo
Handles color calculations, conversions, and transformation logic with improved
error handling and input validation.
"""

import numpy as np
import time
from typing import Tuple, Optional, Dict, Any

# Constants for color calculations
HUE_MAX = 360.0
SATURATION_MAX = 1.0
BRIGHTNESS_MAX = 1.0
FLUORESCENCE_MAX = 1.0
HALO_WIDTH_MIN = 0.02
HALO_WIDTH_MAX = 0.4
HALO_INTENSITY_MAX = 2.0


class ColorEngine:
    """
    Manages color calculations and transformations between neon and anti-neon modes
    """
    
    def __init__(self):
        """Initialize the color engine with default values"""
        # Default values
        self.hue = 0.0  # 0-360 degrees
        self.saturation = 1.0  # 0.0-1.0
        self.brightness = 1.0  # 0.0-1.0
        self.fluorescence = 0.0  # 0.0-1.0 (additional glow effect)
        
        # Neon halo parameters
        self.halo_width = 0.12   # 0.02 - 0.4 (in normalized radius units)
        self.halo_intensity = 1.0  # 0.0 - 2.0
        
        # Current color modes
        self.neon_mode = True
        
        # Animation system
        self.target_hue = 0.0
        self.target_saturation = 1.0
        self.target_brightness = 1.0
        self.target_fluorescence = 0.0
        self.target_neon_mode = True
        
        # Animation state
        self.animation_duration = 0.5  # seconds
        self.animation_start_time = 0
        self.is_animating = False
        
        # Demo mode
        self.demo_mode = False
        self.demo_start_time = 0
        self.demo_duration = 10.0  # seconds for full cycle
        
    def set_hue(self, hue: float) -> None:
        """Set the hue value with validation (0-360 degrees)"""
        if not isinstance(hue, (int, float)):
            raise ValueError(f"Hue must be numeric, got {type(hue).__name__}")
        self.hue = max(0.0, min(HUE_MAX, float(hue)))
        
    def set_saturation(self, saturation: float) -> None:
        """Set the saturation value with validation (0.0-1.0)"""
        if not isinstance(saturation, (int, float)):
            raise ValueError(f"Saturation must be numeric, got {type(saturation).__name__}")
        self.saturation = max(0.0, min(SATURATION_MAX, float(saturation)))
        
    def set_brightness(self, brightness: float) -> None:
        """Set the brightness value with validation (0.0-1.0)"""
        if not isinstance(brightness, (int, float)):
            raise ValueError(f"Brightness must be numeric, got {type(brightness).__name__}")
        self.brightness = max(0.0, min(BRIGHTNESS_MAX, float(brightness)))
        
    def set_fluorescence(self, fluorescence: float) -> None:
        """Set the fluorescence value with validation (0.0-1.0)"""
        if not isinstance(fluorescence, (int, float)):
            raise ValueError(f"Fluorescence must be numeric, got {type(fluorescence).__name__}")
        self.fluorescence = max(0.0, min(FLUORESCENCE_MAX, float(fluorescence)))
        
    def set_neon_mode(self, neon_mode: bool) -> None:
        """Set whether in neon mode (True) or anti-neon mode (False)"""
        if not isinstance(neon_mode, bool):
            raise ValueError(f"Neon mode must be boolean, got {type(neon_mode).__name__}")
        self.neon_mode = neon_mode
        
    def set_halo_width(self, w: float) -> None:
        """Set halo width with validation"""
        if not isinstance(w, (int, float)):
            raise ValueError(f"Halo width must be numeric, got {type(w).__name__}")
        self.halo_width = float(max(HALO_WIDTH_MIN, min(HALO_WIDTH_MAX, w)))
        
    def set_halo_intensity(self, i: float) -> None:
        """Set halo intensity with validation"""
        if not isinstance(i, (int, float)):
            raise ValueError(f"Halo intensity must be numeric, got {type(i).__name__}")
        self.halo_intensity = float(max(0.0, min(HALO_INTENSITY_MAX, i)))
        
    def get_hsv(self) -> Tuple[float, float, float]:
        """Get current HSV values based on mode
        
        Returns:
            Tuple of (hue, saturation, value) as floats
        """
        try:
            if self.neon_mode:
                # Neon mode: high saturation and brightness
                s = self.saturation * (0.8 + 0.2 * self.fluorescence)
                v = self.brightness * (0.8 + 0.2 * self.fluorescence)
            else:
                # Anti-neon mode: low saturation and brightness
                s = self.saturation * 0.3
                v = self.brightness * 0.5
                
            # Ensure values are within valid ranges
            s = max(0.0, min(1.0, s))
            v = max(0.0, min(1.0, v))
            
            return (self.hue, s, v)
        except Exception as e:
            print(f"Error in get_hsv: {e}")
            # Return safe default values
            return (0.0, 0.5, 0.5)
    
    def get_rgb(self) -> Tuple[float, float, float]:
        """Convert current HSV values to RGB (0-1 range)
        
        Returns:
            Tuple of (red, green, blue) as floats in range [0, 1]
        """
        try:
            h, s, v = self.get_hsv()
            return self._hsv_to_rgb(h, s, v)
        except Exception as e:
            print(f"Error in get_rgb: {e}")
            # Return safe default (gray)
            return (0.5, 0.5, 0.5)
    
    def get_bloom_intensity(self):
        """Calculate bloom effect intensity based on current settings"""
        if self.neon_mode:
            # Higher fluorescence = more bloom in neon mode
            return 0.3 + 0.7 * self.fluorescence
        else:
            # Very little bloom in anti-neon mode
            return 0.05
    
    def get_hex_color(self):
        """Get color as hexadecimal string"""
        r, g, b = self.get_rgb()
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def get_color_for_shader(self):
        """Get color as normalized RGB values for shader usage"""
        r, g, b = self.get_rgb()
        return [r, g, b]
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """Convert HSV to RGB with improved error handling
        
        Args:
            h: Hue (0-360)
            s: Saturation (0-1) 
            v: Value/Brightness (0-1)
            
        Returns:
            Tuple of (red, green, blue) as floats in range [0, 1]
        """
        try:
            # Normalize hue to 0-360 range
            h = h % 360.0
            
            # Clamp s and v to valid ranges
            s = max(0.0, min(1.0, s))
            v = max(0.0, min(1.0, v))
            
            # HSV to RGB conversion algorithm
            h_i = int(h / 60) % 6
            f = h / 60 - h_i
            p = v * (1 - s)
            q = v * (1 - f * s)
            t = v * (1 - (1 - f) * s)
            
            if h_i == 0:
                r, g, b = v, t, p
            elif h_i == 1:
                r, g, b = q, v, p
            elif h_i == 2:
                r, g, b = p, v, t
            elif h_i == 3:
                r, g, b = p, q, v
            elif h_i == 4:
                r, g, b = t, p, v
            else:  # h_i == 5
                r, g, b = v, p, q
            
            # Ensure output is in valid range
            return (max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b)))
            
        except Exception as e:
            print(f"Error in HSV to RGB conversion: {e}")
            # Return safe default
            return (0.5, 0.5, 0.5)
    
    def get_halo_rgb(self) -> Tuple[float, float, float]:
        """Compute a bright halo color from current hue with boosted S/V and fluorescence
        
        Returns:
            Tuple of (red, green, blue) as floats for halo color
        """
        try:
            h, _, _ = self.get_hsv()
            s = min(1.0, self.saturation * (0.9 + 0.2 * self.fluorescence))
            v = min(1.0, 0.85 + 0.15 * (self.fluorescence + 0.5))
            return self._hsv_to_rgb(h, s, v)
        except Exception as e:
            print(f"Error in get_halo_rgb: {e}")
            # Return safe default halo color
            return (1.0, 1.0, 1.0)  # White halo as fallback
    
    def animate_to(self, target_hue: Optional[float] = None, target_saturation: Optional[float] = None, 
                   target_brightness: Optional[float] = None, target_fluorescence: Optional[float] = None, 
                   target_neon_mode: Optional[bool] = None, duration: float = 0.5) -> None:
        """Start smooth animation to target values with validation
        
        Args:
            target_hue: Target hue value (0-360), None to keep current
            target_saturation: Target saturation (0-1), None to keep current  
            target_brightness: Target brightness (0-1), None to keep current
            target_fluorescence: Target fluorescence (0-1), None to keep current
            target_neon_mode: Target neon mode, None to keep current
            duration: Animation duration in seconds
        """
        try:
            # Validate duration
            if not isinstance(duration, (int, float)) or duration < 0:
                print(f"Invalid duration {duration}, using default")
                duration = 0.5
                
            self.animation_start_time = time.time()
            self.animation_duration = max(0.1, float(duration))  # Minimum 0.1s
            self.is_animating = True
            
            # Set target values with validation
            if target_hue is not None:
                self.target_hue = max(0.0, min(HUE_MAX, float(target_hue)))
            else:
                self.target_hue = self.hue
                
            if target_saturation is not None:
                self.target_saturation = max(0.0, min(SATURATION_MAX, float(target_saturation)))
            else:
                self.target_saturation = self.saturation
                
            if target_brightness is not None:
                self.target_brightness = max(0.0, min(BRIGHTNESS_MAX, float(target_brightness)))
            else:
                self.target_brightness = self.brightness
                
            if target_fluorescence is not None:
                self.target_fluorescence = max(0.0, min(FLUORESCENCE_MAX, float(target_fluorescence)))
            else:
                self.target_fluorescence = self.fluorescence
                
            if target_neon_mode is not None:
                self.target_neon_mode = bool(target_neon_mode)
            else:
                self.target_neon_mode = self.neon_mode
                
        except Exception as e:
            print(f"Error starting animation: {e}")
            self.is_animating = False
    
    def update_animation(self):
        """Update animation state and interpolate values"""
        if not self.is_animating:
            return
            
        current_time = time.time()
        elapsed = current_time - self.animation_start_time
        progress = min(elapsed / self.animation_duration, 1.0)
        
        # Smooth easing function (ease-out cubic)
        eased_progress = 1.0 - (1.0 - progress) ** 3
        
        # Interpolate values
        self.hue = self._lerp_angle(self.hue, self.target_hue, eased_progress)
        self.saturation = self._lerp(self.saturation, self.target_saturation, eased_progress)
        self.brightness = self._lerp(self.brightness, self.target_brightness, eased_progress)
        self.fluorescence = self._lerp(self.fluorescence, self.target_fluorescence, eased_progress)
        
        # Handle mode switching with a delay
        if progress > 0.5 and self.neon_mode != self.target_neon_mode:
            self.neon_mode = self.target_neon_mode
        
        # Check if animation is complete
        if progress >= 1.0:
            self.is_animating = False
            # Ensure final values are exact
            self.hue = self.target_hue
            self.saturation = self.target_saturation
            self.brightness = self.target_brightness
            self.fluorescence = self.target_fluorescence
            self.neon_mode = self.target_neon_mode
    
    def start_demo_mode(self):
        """Start automatic demo mode with color cycling"""
        self.demo_mode = True
        self.demo_start_time = time.time()
    
    def stop_demo_mode(self):
        """Stop demo mode"""
        self.demo_mode = False
    
    def update_demo(self):
        """Update demo mode - cycle through colors automatically"""
        if not self.demo_mode:
            return
            
        current_time = time.time()
        elapsed = current_time - self.demo_start_time
        cycle_progress = (elapsed % self.demo_duration) / self.demo_duration
        
        # Create interesting color cycles
        # Hue cycles through all colors
        demo_hue = cycle_progress * 360
        
        # Saturation pulses
        demo_saturation = 0.8 + 0.2 * np.sin(cycle_progress * 2 * np.pi)
        
        # Brightness varies
        demo_brightness = 0.7 + 0.3 * np.sin(cycle_progress * 4 * np.pi)
        
        # Fluorescence pulses
        demo_fluorescence = 0.3 + 0.7 * np.sin(cycle_progress * 3 * np.pi)
        
        # Switch modes periodically
        demo_neon_mode = (elapsed // (self.demo_duration / 2)) % 2 == 0
        
        # Animate to demo values
        self.animate_to(
            target_hue=demo_hue,
            target_saturation=demo_saturation,
            target_brightness=demo_brightness,
            target_fluorescence=demo_fluorescence,
            target_neon_mode=demo_neon_mode,
            duration=0.1  # Quick transitions for demo
        )
    
    def _lerp(self, start, end, t):
        """Linear interpolation between two values"""
        return start + (end - start) * t
    
    def _lerp_angle(self, start, end, t):
        """Angular interpolation for hue values (handles wraparound)"""
        # Calculate the shortest path around the color wheel
        diff = (end - start) % 360
        if diff > 180:
            diff -= 360
        
        return (start + diff * t) % 360
    
    # Preset configurations for different neon styles
    PRESETS = {
        "Classic Neon": {
            "hue": 320,  # Magenta
            "saturation": 1.0,
            "brightness": 1.0,
            "fluorescence": 0.8,
            "neon_mode": True
        },
        "Cool Blue": {
            "hue": 210,  # Blue
            "saturation": 0.9,
            "brightness": 0.9,
            "fluorescence": 0.6,
            "neon_mode": True
        },
        "Warm Orange": {
            "hue": 25,   # Orange
            "saturation": 0.95,
            "brightness": 0.95,
            "fluorescence": 0.7,
            "neon_mode": True
        },
        "Electric Green": {
            "hue": 120,  # Green
            "saturation": 1.0,
            "brightness": 0.85,
            "fluorescence": 0.9,
            "neon_mode": True
        },
        "Vaporwave Pink": {
            "hue": 300,  # Pink
            "saturation": 0.8,
            "brightness": 1.0,
            "fluorescence": 0.5,
            "neon_mode": True
        },
        "Cyberpunk Red": {
            "hue": 0,    # Red
            "saturation": 1.0,
            "brightness": 0.8,
            "fluorescence": 1.0,
            "neon_mode": True
        },
        "Anti-Neon Cool": {
            "hue": 200,  # Cool blue
            "saturation": 0.3,
            "brightness": 0.6,
            "fluorescence": 0.1,
            "neon_mode": False
        },
        "Anti-Neon Warm": {
            "hue": 30,   # Warm yellow
            "saturation": 0.2,
            "brightness": 0.5,
            "fluorescence": 0.0,
            "neon_mode": False
        },
           "Neon Brown": {
               "hue": 30,   # orange
               "saturation": 0.7,
               "brightness": 0.35,   # keep core dark to read as brown
            "fluorescence": 0.9,
            "neon_mode": True
        }
    }
    
    @classmethod
    def get_preset_names(cls):
        """Get list of available preset names"""
        return list(cls.PRESETS.keys())
    
    def apply_preset(self, preset_name: str, duration: float = 1.0) -> bool:
        """Apply a preset configuration with animation and validation
        
        Args:
            preset_name: Name of the preset to apply
            duration: Animation duration in seconds
            
        Returns:
            True if preset was applied successfully, False otherwise
        """
        try:
            if not isinstance(preset_name, str):
                print(f"Preset name must be string, got {type(preset_name).__name__}")
                return False
                
            if preset_name not in self.PRESETS:
                print(f"Preset '{preset_name}' not found. Available: {list(self.PRESETS.keys())}")
                return False
                
            preset = self.PRESETS[preset_name]
            
            # Validate preset data
            required_keys = {"hue", "saturation", "brightness", "fluorescence", "neon_mode"}
            if not all(key in preset for key in required_keys):
                print(f"Invalid preset data for '{preset_name}': missing required keys")
                return False
            
            self.animate_to(
                target_hue=preset["hue"],
                target_saturation=preset["saturation"],
                target_brightness=preset["brightness"],
                target_fluorescence=preset["fluorescence"],
                target_neon_mode=preset["neon_mode"],
                duration=duration
            )
            return True
            
        except Exception as e:
            print(f"Error applying preset '{preset_name}': {e}")
            return False
