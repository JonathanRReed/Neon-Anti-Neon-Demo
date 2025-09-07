"""
Color Engine for Neon & Anti-Neon Demo
Handles color calculations, conversions, and transformation logic
"""

import numpy as np
import time


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
        
    def set_hue(self, hue):
        """Set the hue value (0-360 degrees)"""
        self.hue = max(0.0, min(360.0, hue))
        
    def set_saturation(self, saturation):
        """Set the saturation value (0.0-1.0)"""
        self.saturation = max(0.0, min(1.0, saturation))
        
    def set_brightness(self, brightness):
        """Set the brightness value (0.0-1.0)"""
        self.brightness = max(0.0, min(1.0, brightness))
        
    def set_fluorescence(self, fluorescence):
        """Set the fluorescence value (0.0-1.0)"""
        self.fluorescence = max(0.0, min(1.0, fluorescence))
        
    def set_neon_mode(self, neon_mode):
        """Set whether in neon mode (True) or anti-neon mode (False)"""
        self.neon_mode = neon_mode
        
    def set_halo_width(self, w):
        self.halo_width = float(max(0.02, min(0.4, w)))
        
    def set_halo_intensity(self, i):
        self.halo_intensity = float(max(0.0, min(2.0, i)))
        
    def get_hsv(self):
        """Get current HSV values based on mode"""
        if self.neon_mode:
            # Neon mode: high saturation and brightness
            s = self.saturation * (0.8 + 0.2 * self.fluorescence)
            v = self.brightness * (0.8 + 0.2 * self.fluorescence)
        else:
            # Anti-neon mode: low saturation and brightness
            s = self.saturation * 0.3
            v = self.brightness * 0.5
            
        return (self.hue, s, v)
    
    def get_rgb(self):
        """Convert current HSV values to RGB (0-1 range)"""
        h, s, v = self.get_hsv()
        
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
        else:
            r, g, b = v, p, q
            
        return (r, g, b)
    
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
    
    def _hsv_to_rgb(self, h, s, v):
        h_i = int(h / 60) % 6
        f = h / 60 - h_i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        if h_i == 0:
            return v, t, p
        elif h_i == 1:
            return q, v, p
        elif h_i == 2:
            return p, v, t
        elif h_i == 3:
            return p, q, v
        elif h_i == 4:
            return t, p, v
        else:
            return v, p, q
    
    def get_halo_rgb(self):
        """Compute a bright halo color from current hue with boosted S/V and fluorescence"""
        h, _, _ = self.get_hsv()
        s = min(1.0, self.saturation * (0.9 + 0.2 * self.fluorescence))
        v = min(1.0, 0.85 + 0.15 * (self.fluorescence + 0.5))
        return self._hsv_to_rgb(h, s, v)
    
    def animate_to(self, target_hue=None, target_saturation=None, target_brightness=None, 
                   target_fluorescence=None, target_neon_mode=None, duration=0.5):
        """Start smooth animation to target values"""
        self.animation_start_time = time.time()
        self.animation_duration = duration
        self.is_animating = True
        
        if target_hue is not None:
            self.target_hue = max(0.0, min(360.0, target_hue))
        if target_saturation is not None:
            self.target_saturation = max(0.0, min(1.0, target_saturation))
        if target_brightness is not None:
            self.target_brightness = max(0.0, min(1.0, target_brightness))
        if target_fluorescence is not None:
            self.target_fluorescence = max(0.0, min(1.0, target_fluorescence))
        if target_neon_mode is not None:
            self.target_neon_mode = target_neon_mode
    
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
    
    def apply_preset(self, preset_name, duration=1.0):
        """Apply a preset configuration with animation"""
        if preset_name not in self.PRESETS:
            print(f"Preset '{preset_name}' not found")
            return False
            
        preset = self.PRESETS[preset_name]
        self.animate_to(
            target_hue=preset["hue"],
            target_saturation=preset["saturation"],
            target_brightness=preset["brightness"],
            target_fluorescence=preset["fluorescence"],
            target_neon_mode=preset["neon_mode"],
            duration=duration
        )
        return True
