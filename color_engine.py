"""
Color Engine for Neon & Anti-Neon Demo
Handles color calculations, conversions, and transformation logic
"""

import numpy as np


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
        
        # Current color modes
        self.neon_mode = True
        
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
    
    def calculate_complementary_color(self):
        """Calculate complementary color (opposite on the color wheel)"""
        h = (self.hue + 180) % 360
        return h, self.saturation, self.brightness
