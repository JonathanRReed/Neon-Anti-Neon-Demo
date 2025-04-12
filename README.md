# Neon & Anti-Neon Demo (OpenGL / Python)

This was inspired by a video from [Vsaucse](https://www.youtube.com/shorts/vnpOGuvZsX0)

This is was made as a practice project, its an interactive physics-inspired real-time simulation of neon colors & their desaturated "anti-neon" counterparts using ModernGL & Dear PyGui.

Feel free to use, modify, and distribute this code as you see fit. I'll not be held responsible for any issues that may arise from using this code or continue to maintain it.

## Features

- Interactive hue slider for color selection
- Real-time adjustment of saturation, brightness, & fluorescence
- Neon and anti-neon visual modes with shader effects
- Modern dark-themed UI

## Requirements

- Python 3.8+
- ModernGL
- Dear PyGui
- NumPy
- PyWavefront

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the main application:

```bash
python main.py
```

### Controls

- **Hue Slider**: Click and drag to select color hue
- **Saturation Slider**: Adjust color saturation (high for neon, low for anti-neon)
- **Brightness Slider**: Control light intensity
- **Fluorescence Toggle**: Enable/disable extra glow effect in neon mode

## Project Structure

- `main.py`: Entry point of the application
- `color_engine.py`: Color calculation and simulation engine
- `ui.py`: Dear PyGui user interface components
- `shaders/`: GLSL shader files for rendering effects
- `assets/`: Additional resources (if applicable)

## License

MIT License

Copyright (c) 2025 Jonathan Ray Reed

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
