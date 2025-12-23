"""
Chimerical Colors Module - Afterimage-Induced "Impossible" Color Experiences

This module implements demonstrations of chimerical (impossible) colors:
- Stygian Colors: colors that appear darker than black
- Self-Luminous Colors: colors that appear brighter than white
- Hyperbolic Colors: colors that appear more saturated than possible

These effects require prolonged viewing of adapting stimuli and are
produced by afterimage induction.

WARNING: Extended viewing of saturated colors can cause visual fatigue.
Take breaks if needed.

References:
- Crane, H. D., & Piantanida, T. P. (1983). On Seeing Reddish Green and 
  Yellowish Blue. Science, 221(4615), 1078-1080.
- Churchland, P. S. (2005). Chimerical Colors: Some Phenomenological 
  Predictions from Cognitive Neuroscience. Philosophical Psychology.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Callable
from dataclasses import dataclass
from enum import Enum
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from color_management import ColorManagement, srgb_to_linear, linear_to_srgb
from modules import register_module


class ChimericalType(Enum):
    """Types of chimerical color experiences."""
    STYGIAN = "stygian"          # Darker than black
    SELF_LUMINOUS = "self_luminous"  # Brighter than white (glowing)
    HYPERBOLIC = "hyperbolic"    # More saturated than possible


@dataclass
class ChimericalParams:
    """Parameters for chimerical color demonstrations."""
    # Type of chimerical experience
    effect_type: ChimericalType = ChimericalType.SELF_LUMINOUS
    
    # Adaptation parameters
    adapting_hue: float = 180.0  # Cyan (complement of red for red afterimage)
    adapting_saturation: float = 1.0
    adaptation_duration: float = 45.0  # seconds
    
    # Display settings
    fixation_size: int = 10
    
    # Derived: test field color depends on effect type
    # Stygian: black background
    # Self-luminous: white background
    # Hyperbolic: same hue as afterimage


@register_module
class ChimericalModule:
    """
    Interactive demonstration of chimerical (impossible) color experiences.
    
    Chimerical colors are perceptual experiences that cannot be produced by
    any physical light source. They arise from afterimage induction:
    
    1. ADAPTATION: Gaze at a saturated color field for 30-60 seconds
    2. TEST: View test field - afterimage creates impossible percept
    
    Safety: Extended viewing of saturated colors can cause fatigue.
    """
    
    def __init__(self, params: Optional[ChimericalParams] = None):
        self.params = params or ChimericalParams()
        self.is_adapting = False
        self.adaptation_start_time = 0
        self.adaptation_complete = False
        self._on_adaptation_complete: Optional[Callable] = None
    
    @property
    def name(self) -> str:
        return "Chimerical Colors: Afterimage Experiences"
    
    @property
    def description(self) -> str:
        type_desc = {
            ChimericalType.STYGIAN: "Stygian colors appear darker than black",
            ChimericalType.SELF_LUMINOUS: "Self-luminous colors appear to glow brighter than white",
            ChimericalType.HYPERBOLIC: "Hyperbolic colors appear impossibly saturated"
        }
        return type_desc.get(self.params.effect_type, "Afterimage-induced color experiences")
    
    @property
    def has_safety_warning(self) -> bool:
        return True  # Requires user awareness of visual fatigue
    
    def get_safety_warning(self) -> str:
        """Get safety warning text."""
        return (
            "[!] VISUAL FATIGUE WARNING [!]\n"
            "\n"
            "This demonstration requires staring at a saturated color\n"
            "for 30-60 seconds to induce an afterimage effect.\n"
            "\n"
            "- Do not use if prone to headaches or visual strain\n"
            "- Blink normally during adaptation\n"
            "- Look away if you experience any discomfort\n"
            "- Take breaks between trials\n"
            "\n"
            "The effect is temporary and harmless for most viewers."
        )
    
    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[float, float, float]:
        """Convert HSL to RGB."""
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
    
    def get_adapting_color(self) -> Tuple[float, float, float]:
        """Get the adapting field color."""
        return self._hsl_to_rgb(
            self.params.adapting_hue,
            self.params.adapting_saturation,
            0.5  # Mid lightness for best saturation
        )
    
    def get_afterimage_hue(self) -> float:
        """Get the expected afterimage hue (complement of adapting color)."""
        return (self.params.adapting_hue + 180) % 360
    
    def get_test_field_color(self) -> Tuple[float, float, float]:
        """Get the test field color based on effect type."""
        effect_type = self.params.effect_type
        
        if effect_type == ChimericalType.STYGIAN:
            # Black background - afterimage appears darker than black
            return (0.0, 0.0, 0.0)
        elif effect_type == ChimericalType.SELF_LUMINOUS:
            # White background - afterimage appears to glow
            return (1.0, 1.0, 1.0)
        elif effect_type == ChimericalType.HYPERBOLIC:
            # Same hue as afterimage but desaturated - afterimage appears super-saturated
            afterimage_hue = self.get_afterimage_hue()
            return self._hsl_to_rgb(afterimage_hue, 0.3, 0.5)
        else:
            return (0.5, 0.5, 0.5)
    
    def start_adaptation(self):
        """Start the adaptation timer."""
        self.is_adapting = True
        self.adaptation_start_time = time.time()
        self.adaptation_complete = False
    
    def update(self) -> float:
        """
        Update adaptation state.
        
        Returns:
            Remaining time in seconds (0 if complete)
        """
        if not self.is_adapting:
            return self.params.adaptation_duration
        
        elapsed = time.time() - self.adaptation_start_time
        remaining = max(0, self.params.adaptation_duration - elapsed)
        
        if remaining == 0 and not self.adaptation_complete:
            self.adaptation_complete = True
            self.is_adapting = False
            if self._on_adaptation_complete:
                self._on_adaptation_complete()
        
        return remaining
    
    def reset(self):
        """Reset the adaptation state."""
        self.is_adapting = False
        self.adaptation_start_time = 0
        self.adaptation_complete = False
    
    def render_adaptation_screen(self, width: int, height: int) -> np.ndarray:
        """Render the adaptation screen with fixation cross."""
        adapting_color = self.get_adapting_color()
        
        # Fill with adapting color
        image = np.zeros((height, width, 3), dtype=np.float32)
        image[:, :, 0] = adapting_color[0]
        image[:, :, 1] = adapting_color[1]
        image[:, :, 2] = adapting_color[2]
        
        # Draw fixation cross in contrasting color
        cx, cy = width // 2, height // 2
        fix_size = self.params.fixation_size
        fix_width = 2
        
        # Use black or white depending on adapting color brightness
        avg_brightness = sum(adapting_color) / 3
        fix_color = 0.0 if avg_brightness > 0.5 else 1.0
        
        # Horizontal bar
        image[cy-fix_width:cy+fix_width, cx-fix_size:cx+fix_size] = fix_color
        # Vertical bar
        image[cy-fix_size:cy+fix_size, cx-fix_width:cx+fix_width] = fix_color
        
        return image
    
    def render_test_screen(self, width: int, height: int) -> np.ndarray:
        """Render the test screen for afterimage viewing."""
        test_color = self.get_test_field_color()
        
        # Fill with test color
        image = np.zeros((height, width, 3), dtype=np.float32)
        image[:, :, 0] = test_color[0]
        image[:, :, 1] = test_color[1]
        image[:, :, 2] = test_color[2]
        
        # Small fixation dot
        cx, cy = width // 2, height // 2
        dot_size = 3
        
        # Contrasting dot color
        avg_brightness = sum(test_color) / 3
        dot_color = 0.0 if avg_brightness > 0.5 else 1.0
        
        # Draw small fixation dot
        for dy in range(-dot_size, dot_size + 1):
            for dx in range(-dot_size, dot_size + 1):
                if dx*dx + dy*dy <= dot_size*dot_size:
                    y, x = cy + dy, cx + dx
                    if 0 <= y < height and 0 <= x < width:
                        image[y, x] = dot_color
        
        return image
    
    def render(self, width: int, height: int) -> np.ndarray:
        """Render current state (adaptation or test screen)."""
        if self.is_adapting:
            return self.render_adaptation_screen(width, height)
        elif self.adaptation_complete:
            return self.render_test_screen(width, height)
        else:
            # Initial state - show adaptation screen preview
            return self.render_adaptation_screen(width, height)
    
    def get_proof_info(self) -> str:
        """Information about the effect."""
        effect_type = self.params.effect_type
        adapting_hex = ColorManagement.rgb_to_hex(np.array(self.get_adapting_color()))
        test_hex = ColorManagement.rgb_to_hex(np.array(self.get_test_field_color()))
        afterimage_hue = self.get_afterimage_hue()
        
        type_names = {
            ChimericalType.STYGIAN: "Stygian (darker than black)",
            ChimericalType.SELF_LUMINOUS: "Self-Luminous (brighter than white)",
            ChimericalType.HYPERBOLIC: "Hyperbolic (impossibly saturated)"
        }
        
        return (
            f"--- CHIMERICAL COLOR SETUP ---\n"
            f"Effect Type: {type_names[effect_type]}\n"
            f"\n"
            f"Adapting Color: {adapting_hex} (hue {self.params.adapting_hue:.0f}°)\n"
            f"Expected Afterimage: ~{afterimage_hue:.0f}° hue\n"
            f"Test Background: {test_hex}\n"
            f"\n"
            f"Duration: {self.params.adaptation_duration:.0f} seconds"
        )
    
    def get_explanation(self) -> str:
        """Get scientific explanation of the effect."""
        effect_type = self.params.effect_type
        
        base_explanation = (
            "HOW CHIMERICAL COLORS WORK\n"
            "--------------------------\n"
            "\n"
            "After prolonged viewing of a color, the photoreceptors sensitive\n"
            "to that color become fatigued (adapted). When you then look at\n"
            "a neutral or contrasting field, the OTHER photoreceptors\n"
            "respond more strongly, creating an afterimage in the\n"
            "complementary color.\n"
            "\n"
        )
        
        type_explanations = {
            ChimericalType.STYGIAN: (
                "STYGIAN COLORS\n"
                "On a black field, the afterimage appears as a color that\n"
                "seems darker than black - an impossible deep, dark hue.\n"
                "This occurs because the adapted channels are suppressed\n"
                "below their normal dark baseline."
            ),
            ChimericalType.SELF_LUMINOUS: (
                "SELF-LUMINOUS COLORS\n"
                "On a white field, the afterimage appears to glow with\n"
                "an impossible brightness. The non-adapted channels\n"
                "respond to the white light while adapted channels\n"
                "remain suppressed, creating an 'impossible' luminance\n"
                "contrast within the perceived color."
            ),
            ChimericalType.HYPERBOLIC: (
                "HYPERBOLIC COLORS\n"
                "On a desaturated field of the same hue as the afterimage,\n"
                "the color appears impossibly saturated - more vivid than\n"
                "any color that could be produced by physical light.\n"
                "This is because the afterimage adds saturation on top\n"
                "of the physical stimulus."
            )
        }
        
        return base_explanation + type_explanations.get(effect_type, "")
    
    def set_effect_type(self, effect_type: ChimericalType):
        """Change the effect type."""
        self.params.effect_type = effect_type
        self.reset()
    
    def set_adapting_hue(self, hue: float):
        """Change the adapting hue."""
        self.params.adapting_hue = hue % 360
        self.reset()


# Quick presets for different effects
# Research: optimal adaptation time is 20-60 seconds
CHIMERICAL_PRESETS = {
    "Stygian Blue": ChimericalParams(
        effect_type=ChimericalType.STYGIAN,
        adapting_hue=60,  # Yellow adapts → blue afterimage on black = stygian blue
        adapting_saturation=1.0,
        adaptation_duration=30  # 30s is within optimal 20-60s range
    ),
    "Self-Luminous Red": ChimericalParams(
        effect_type=ChimericalType.SELF_LUMINOUS,
        adapting_hue=180,  # Cyan adapts → red afterimage on white = glowing red
        adapting_saturation=1.0,
        adaptation_duration=30
    ),
    "Hyperbolic Orange": ChimericalParams(
        effect_type=ChimericalType.HYPERBOLIC,
        adapting_hue=210,  # Blue-cyan adapts → orange afterimage
        adapting_saturation=1.0,
        adaptation_duration=30
    ),
    "Stygian Green": ChimericalParams(
        effect_type=ChimericalType.STYGIAN,
        adapting_hue=300,  # Magenta adapts → green afterimage on black
        adapting_saturation=1.0,
        adaptation_duration=30
    ),
}


# Test when run directly
if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    # Test each effect type
    fig, axes = plt.subplots(3, 2, figsize=(10, 12))
    
    for (name, params), (ax_adapt, ax_test) in zip(
        CHIMERICAL_PRESETS.items(),
        [(axes[i, 0], axes[i, 1]) for i in range(3)]
    ):
        module = ChimericalModule(params)
        
        adapt_img = module.render_adaptation_screen(400, 300)
        test_img = module.render_test_screen(400, 300)
        
        ax_adapt.imshow(adapt_img)
        ax_adapt.set_title(f"{name}\nAdaptation Screen")
        ax_adapt.axis('off')
        
        ax_test.imshow(test_img)
        ax_test.set_title(f"{name}\nTest Screen")
        ax_test.axis('off')
    
    # Use last row for info
    axes[2, 0].axis('off')
    axes[2, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig('chimerical_colors_test.png', dpi=150)
    print("Saved test image to chimerical_colors_test.png")
    
    # Print info for first preset
    module = ChimericalModule(CHIMERICAL_PRESETS["Self-Luminous Red"])
    print("\n" + module.get_safety_warning())
    print("\n" + module.get_proof_info())
    print("\n" + module.get_explanation())
