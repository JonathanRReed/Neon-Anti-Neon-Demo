# Neon & Anti-Neon Demo (OpenGL / Python)

Inspired by the Vsauce short on neon/brown color perception.

An interactive real‑time simulation of neon colors and their “anti‑neon” counterparts, featuring a liquid‑glass UI, GPU shaders (with automatic CPU fallback), dual‑color core/halo neon rendering, smooth animations, and one‑click presets (including “Neon Brown”).

Feel free to use, modify, and distribute this code as you see fit. I will not be held responsible for any issues that may arise from using this code or continue to maintain it.

## Features

- Interactive liquid‑glass UI using Dear PyGui
- Real‑time sliders: Hue, Saturation, Brightness, Fluorescence
- Neon and Anti‑Neon modes
- Dual‑color neon shader (core + halo) with Halo Width and Halo Intensity controls
- Presets: Classic Neon, Cool Blue, Warm Orange, Electric Green, Vaporwave Pink, Cyberpunk Red, Anti‑Neon Cool, Anti‑Neon Warm, Neon Brown
- GPU acceleration via ModernGL (auto‑fallback to CPU if no GL context is available)
- Bottom info panel with FPS, Renderer mode, and current color state
- Export current frame to PNG (`exports/`)

## Requirements

- Python 3.13 (tested) or 3.10+
- See `requirements.txt` (ModernGL, Dear PyGui 2.x, NumPy, GLFW, Pillow, PyWavefront)

## Installation

1. Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python main.py
```

Notes:
- On some macOS systems, Dear PyGui’s context may not expose a GL 3.3 context. The app will automatically switch to CPU rendering and continue running.
- Use the Renderer toggle (GPU/CPU) in the UI to force modes as needed.

### Controls

- Hue / Saturation / Brightness / Fluorescence sliders
- Halo Width / Halo Intensity sliders (neon look)
- Mode: Neon / Anti‑Neon
- Preset buttons (including Neon Brown)
- Export Image (PNG)
- Reset

## Project Structure

- `main.py` — Application entry point (UI + rendering + export)
- `color_engine.py` — Color state, animations, presets, halo computation
- `shaders/` — GLSL vertex/fragment shaders (neon and anti‑neon)
- `exports/` — Saved PNGs (created on first export)
- `legacy/ui.py` — Previous experimental UI (kept for reference)

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
