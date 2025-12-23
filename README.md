# Color Perception Laboratory (Neon & Anti-Neon Demo)

Inspired by the Vsauce short on neon/brown color perception.
[Vsauce Neon/Brown](https://www.youtube.com/shorts/vnpOGuvZsX0)

An interactive **Color Perception Laboratory** featuring real-time neon color simulation, classic color illusions with scientific explanations, and validation tools to prove that perception is relative. This implementation uses a highly optimized NumPy-based rendering engine for smooth interaction.

Feel free to use, modify, and distribute this code as you see fit. I will not be held responsible for any issues that may arise from using this code.

## Core Features

### Original Neon Demo
- Interactive UI using Dear PyGui
- Real-time sliders: Hue, Saturation, Brightness, Fluorescence
- Neon and Anti-Neon modes with pulsing/flicker shader effects
- Dual-color neon shader (core + halo) with adjustable parameters
- 13 Presets: Classic Neon, Synthwave Sunset, Matrix Green, Neon Brown, and more
- GPU acceleration via ModernGL (auto-fallback to high-performance CPU path)
- Demo mode with auto-cycling colors
- Keyboard shortcuts for quick control

### High-Performance Rendering
- **Vectorized Logic**: All illusion modules are implemented using vectorized NumPy operations, eliminating Python loops and achieving up to 100x speedup.
- **Dynamic Textures**: Direct 1D array updates to Dear PyGui textures for low-latency visual feedback.
- **Robust Fallback**: Seamless transition between GPU (OpenGL) and CPU rendering paths.

### Color Perception Modules

| Module | Description |
|--------|-------------|
| **Neon Brown** | Demonstrates how same RGB appears orange OR brown based on surround luminance. |
| **Simultaneous Contrast** | Identical gray patches appear different on high-contrast backgrounds. |
| **Checker Shadow** | Adelson's famous illusion - squares A and B are identical! Updated with realistic cylinder shadow. |
| **Cornsweet Edge** | 15% contrast edge gradient makes identical regions look significantly different. |
| **Neon Spreading** | Ehrenstein radial lines with colored inducers create an illusory "neon" glow. |
| **Chimerical Colors** | Afterimage-induced "impossible" colors (Stygian Blue, Self-Luminous Red, etc.). |
| **Lilac Chaser** | Rotating gap in 12 magenta discs creates a green afterimage "pac-man". |
| **Benham's Disk** | Optimized 5Hz B/W rotation produces subjective (Fechner) colors. |

### Scientific & Validation Tools
- **Pixel Proof Mode**: Overlay squares to visually verify that illusory regions have identical RGB values.
- **sRGB/Linear Color Management**: Physically correct blending and inverse gamma operations.
- **Eyedropper Tool**: Real-time sampling of any pixel for HEX, sRGB, and linear values.
- **Scientific Explanations**: Detailed descriptions of the physiological mechanisms behind each effect.

## Requirements

- Python 3.10+ (tested on 3.13)
- Required libraries: `dearpygui`, `numpy`, `moderngl`, `pillow` (see `requirements.txt`)

## Installation

1. Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run the main application:

```bash
python main.py
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Toggle Neon / Anti-Neon mode |
| `R` | Reset to defaults |
| `Left` / `Right` | Adjust hue (plus/minus 15 degrees) |
| `Up` / `Down` | Adjust brightness (plus/minus 10%) |
| `D` | Toggle Demo mode |
| `1`-`9` | Apply preset by number |

### Verification Tests

The project includes a comprehensive test suite for color correctness and performance:

```bash
python test_basic.py           # Core logic tests (9 passed)
python test_color_management.py # Scientific management tests (7 passed)
```

## Project Structure

- `main.py`: Application entry point and UI orchestration.
- `color_engine.py`: State management, presets, and animation logic.
- `color_management.py`: Scientific color space conversions and appearance models.
- `validation_tools.py`: Pixel sampling and proof overlay logic.
- `modules/`: Individual illusion implementations (vectorized).
- `shaders/`: GLSL fragment shaders for advanced neon effects.

## Safety Notices

[!] Some modules include safety warnings:
- **Chimerical Colors**: Extended viewing of saturated colors can cause visual fatigue.
- **Benham's Disk / Motion Illusions**: Rotating patterns may affect photosensitive viewers. Do not use if prone to seizures or severe motion sensitivity.

## Scientific References

- Brown perception: [Context-dependent color naming (PubMed)](https://pubmed.ncbi.nlm.nih.gov/37133023/)
- Simultaneous contrast: [Pressbooks - Sensation and Perception](https://pressbooks.umn.edu/sensationandperception/chapter/simultaneous-contrast/)
- Chimerical colors: [PhilPapers - Chimerical Colors](https://philpapers.org/rec/CHUCCS)
- Neon spreading: [Boston University - Filling-in Models](https://sites.bu.edu/steveg/files/2016/06/PinGro2005JOSA.pdf)
- Cornsweet Effect: [Wolfram Research - Cornsweet Illusion](https://demonstrations.wolfram.com/TheCornsweetIllusion/)

## License

MIT License

Copyright (c) 2025 Jonathan Ray Reed
