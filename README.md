# Color perception lab

Adjust neon effects and explore color illusions in a Python desktop app. Inspired by [Vsauce's neon and brown demonstration](https://www.youtube.com/shorts/vnpOGuvZsX0).

The app uses Dear PyGui, NumPy, ModernGL, and Pillow. GPU rendering falls back to a CPU path when needed. Pixel sampling and comparison overlays let you inspect the colors used to draw an illusion.

## Install and run

Requires Python 3.10+, tested on 3.13.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On Windows, activate with `.venv\Scripts\activate` instead.

## Explore

The original neon demo has hue, saturation, brightness, and fluorescence controls, core and halo colors, pulsing effects, presets, and an automatic color cycle.

| Module | Demonstration |
| --- | --- |
| Neon Brown | One RGB value appears orange or brown against different surroundings |
| Simultaneous Contrast | Identical gray patches against different backgrounds |
| Checker Shadow | Equal-valued squares in a drawn shadow scene |
| Cornsweet Edge | An edge gradient changes the apparent brightness of neighboring regions |
| Neon Spreading | Colored line segments produce an apparent glow |
| Chimerical Colors | Saturated-color afterimages |
| Lilac Chaser | A moving gap among magenta discs |
| Benham's Disk | Subjective colors from a rotating black-and-white pattern |

Pixel Proof overlays compare RGB values. The eyedropper reports HEX, sRGB, and linear values. Explanatory notes accompany the effects. NumPy operations, texture updates, and sRGB-to-linear conversions support rendering.

| Key | Action |
| --- | --- |
| `Space` | Toggle Neon and Anti-Neon |
| `R` | Reset |
| `Left` / `Right` | Change hue by 15 degrees |
| `Up` / `Down` | Change brightness by 10% |
| `D` | Toggle automatic demo mode |
| `1` through `9` | Select a preset |

## Safety

Some effects pulse, flicker, or rotate. Do not use the motion effects if you are prone to seizures or severe motion sensitivity. Prolonged viewing of saturated-color afterimages can cause visual fatigue.

## Develop

```bash
python test_basic.py
python test_color_management.py
```

| Path | Contents |
| --- | --- |
| `main.py` | App entry and UI |
| `color_engine.py` | State, presets, and animation |
| `color_management.py` | Color conversions and appearance models |
| `validation_tools.py` | Sampling and comparison overlays |
| `modules/` | Illusion implementations |
| `shaders/` | GLSL neon effects |

## References

[Brown perception](https://pubmed.ncbi.nlm.nih.gov/37133023/) · [Simultaneous contrast](https://pressbooks.umn.edu/sensationandperception/chapter/simultaneous-contrast/) · [Chimerical colors](https://philpapers.org/rec/CHUCCS) · [Neon spreading](https://sites.bu.edu/steveg/files/2016/06/PinGro2005JOSA.pdf) · [Cornsweet illusion](https://demonstrations.wolfram.com/TheCornsweetIllusion/)

## License

MIT License

Copyright (c) 2025 Jonathan Ray Reed
