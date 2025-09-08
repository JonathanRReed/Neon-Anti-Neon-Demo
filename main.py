"""
Neon & Anti-Neon Demo
Main application that integrates all components
"""

import numpy as np
import dearpygui.dearpygui as dpg
import time
import os
import sys
from datetime import datetime
from PIL import Image

from color_engine import ColorEngine

# Constants
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_RENDER_WIDTH = 800
DEFAULT_RENDER_HEIGHT = 600
TARGET_FPS = 60.0
MAX_FRAME_SKIP = 2
FPS_UPDATE_INTERVAL = 10  # Update FPS display every N frames
FRAME_TIME_SAMPLES = 10   # Number of frame times to average for FPS calculation

# UI Constants
CONTROL_PANEL_WIDTH = 380
RENDER_PANEL_WIDTH = 800
INFO_PANEL_WIDTH = 1180
INFO_PANEL_HEIGHT = 160
SLIDER_WIDTH = 350
PRESET_BUTTON_WIDTH = 105

# Export Constants
DEFAULT_EXPORT_DIR = "exports"
EXPORT_IMAGE_FORMAT = "PNG"

# Performance Constants
CPU_THROTTLE_SLEEP = 0.001  # Sleep time when running > 200 FPS
HIGH_FPS_THRESHOLD = 200.0
LOW_FPS_THRESHOLD = 30.0
GOOD_FPS_THRESHOLD = 50.0

# Try to import ModernGL, handle gracefully if not available
try:
    import moderngl as mgl
    MODERNGL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ModernGL not available: {e}")
    print("Application will run in CPU-only mode.")
    mgl = None
    MODERNGL_AVAILABLE = False


class ShaderRenderer:
    """
    GPU-accelerated renderer using ModernGL and GLSL shaders
    """
    
    def __init__(self, width=DEFAULT_RENDER_WIDTH, height=DEFAULT_RENDER_HEIGHT):
        """Initialize the shader renderer (context will be created lazily)"""
        if not MODERNGL_AVAILABLE:
            raise RuntimeError("ModernGL is not available - cannot create GPU renderer")
            
        self.width = width
        self.height = height
        self.ctx = None
        self.neon_program = None
        self.antineon_program = None
        self.vbo = None
        self.vao = None
        self.framebuffer = None
        self._initialization_failed = False
    
    def _ensure_context(self):
        """Create ModernGL context and GPU resources if not already created.
        This must be called after DearPyGui has shown the viewport so an OpenGL
        context is current.
        
        Raises:
            RuntimeError: If OpenGL context creation or shader loading fails
        """
        if self.ctx is not None or self._initialization_failed:
            return
            
        try:
            # Attach to the current OpenGL context provided by DearPyGui
            self.ctx = mgl.create_context(require=330)
            print(f"OpenGL Context: {self.ctx.version_code}")
            
            # Load shaders and GPU buffers
            self._load_shaders()
            self._create_quad()
            self.framebuffer = self.ctx.framebuffer(
                color_attachments=[self.ctx.texture((self.width, self.height), 4, dtype='f4')]
            )
            print("GPU renderer initialized successfully")
            
        except Exception as e:
            self._initialization_failed = True
            print(f"Failed to initialize GPU renderer: {e}")
            raise RuntimeError(f"GPU initialization failed: {e}") from e
        
    def _load_shaders(self):
        """Load GLSL shaders from files
        
        Raises:
            FileNotFoundError: If shader files are missing
            RuntimeError: If shader compilation fails
        """
        shader_files = {
            'vertex': 'shaders/vertex.glsl',
            'neon_fragment': 'shaders/neon_fragment.glsl', 
            'antineon_fragment': 'shaders/antineon_fragment.glsl'
        }
        
        shaders = {}
        
        try:
            # Load all shader files
            for shader_type, filepath in shader_files.items():
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"Shader file not found: {filepath}")
                    
                with open(filepath, 'r', encoding='utf-8') as f:
                    shaders[shader_type] = f.read()
                    
            # Create shader programs with error handling
            try:
                self.neon_program = self.ctx.program(
                    vertex_shader=shaders['vertex'],
                    fragment_shader=shaders['neon_fragment']
                )
            except Exception as e:
                raise RuntimeError(f"Failed to compile neon shader program: {e}") from e
                
            try:
                self.antineon_program = self.ctx.program(
                    vertex_shader=shaders['vertex'],
                    fragment_shader=shaders['antineon_fragment']
                )
            except Exception as e:
                raise RuntimeError(f"Failed to compile anti-neon shader program: {e}") from e
                
            print("Shaders loaded and compiled successfully")
            
        except FileNotFoundError as e:
            print(f"Shader loading failed: {e}")
            raise
        except Exception as e:
            print(f"Shader compilation failed: {e}")
            raise RuntimeError(f"Shader setup failed: {e}") from e
    
    def _create_quad(self):
        """Create a full-screen quad for rendering"""
        # Quad vertices (positions and texture coordinates)
        vertices = np.array([
            # positions    # texture coords
            -1.0, -1.0,    0.0, 0.0,  # bottom left
             1.0, -1.0,    1.0, 0.0,  # bottom right
            -1.0,  1.0,    0.0, 1.0,  # top left
             1.0,  1.0,    1.0, 1.0,  # top right
        ], dtype=np.float32)
        
        # Create vertex buffer
        self.vbo = self.ctx.buffer(vertices.tobytes())
        
        # Create vertex array
        self.vao = self.ctx.vertex_array(
            self.neon_program,  # We'll switch programs as needed
            [(self.vbo, '2f 2f', 'in_position', 'in_texcoord')]
        )
    
    def render_frame(self, color_engine):
        """Render a frame using shaders
        
        Args:
            color_engine: ColorEngine instance with current color state
            
        Returns:
            np.ndarray: Rendered frame as float32 RGBA array
            
        Raises:
            RuntimeError: If rendering fails
        """
        try:
            # Ensure GL context and resources are ready
            self._ensure_context()
            
            # Bind framebuffer
            self.framebuffer.use()
            self.ctx.clear(0.05, 0.05, 0.05, 1.0)  # Dark background
            
            # Choose shader program based on mode
            if color_engine.neon_mode:
                program = self.neon_program
                # Set neon shader uniforms (dual-color core/halo)
                cr, cg, cb = color_engine.get_rgb()
                hr, hg, hb = color_engine.get_halo_rgb()
                program['core_color'] = (cr, cg, cb)
                program['halo_color'] = (hr, hg, hb)
                program['halo_width'] = float(color_engine.halo_width)
                program['halo_intensity'] = float(color_engine.halo_intensity)
                program['bloom_intensity'] = float(color_engine.get_bloom_intensity())
            else:
                program = self.antineon_program
                r, g, b = color_engine.get_rgb()
                program['color'] = (r, g, b)
                program['shadow_intensity'] = 0.5  # Adjust as needed
            
            # Bind vertex array with current program
            vao = self.ctx.vertex_array(program, [(self.vbo, '2f 2f', 'in_position', 'in_texcoord')])
            
            # Render quad
            vao.render(mgl.TRIANGLE_STRIP)
            
            # Read pixels from framebuffer
            pixels = self.framebuffer.read(components=4, dtype='f4')
            
            # Convert to numpy array and reshape
            texture_data = np.frombuffer(pixels, dtype=np.float32).reshape(self.height, self.width, 4)
            
            return texture_data
            
        except Exception as e:
            print(f"Frame rendering failed: {e}")
            raise RuntimeError(f"GPU rendering error: {e}") from e
    
    def cleanup(self):
        """Clean up ModernGL resources (safe even if context failed)"""
        try:
            if getattr(self, 'vao', None) is not None:
                self.vao.release()
        except Exception:
            pass
        try:
            if getattr(self, 'vbo', None) is not None:
                self.vbo.release()
        except Exception:
            pass
        try:
            if getattr(self, 'framebuffer', None) is not None:
                self.framebuffer.release()
        except Exception:
            pass
        try:
            if getattr(self, 'neon_program', None) is not None:
                self.neon_program.release()
        except Exception:
            pass
        try:
            if getattr(self, 'antineon_program', None) is not None:
                self.antineon_program.release()
        except Exception:
            pass
        try:
            if getattr(self, 'ctx', None) is not None:
                self.ctx.release()
        except Exception:
            pass


class NeonApp:
    """
    Main application class that integrates all components
    """
    
    def __init__(self):
        """Initialize the application with comprehensive error handling"""
        print("Initializing Neon & Anti-Neon Demo...")
        
        try:
            # Create color engine
            self.color_engine = ColorEngine()
            
            # Initialize DearPyGui with error handling
            try:
                dpg.create_context()
                dpg.create_viewport(
                    title="Neon & Anti-Neon Demo", 
                    width=DEFAULT_WINDOW_WIDTH, 
                    height=DEFAULT_WINDOW_HEIGHT
                )
            except Exception as e:
                print(f"Failed to initialize Dear PyGui: {e}")
                raise RuntimeError(f"GUI initialization failed: {e}") from e
            
            # Initialize fonts with better error handling
            self._initialize_fonts()
            
            # Set up theme
            self._setup_theme()
            
            # Setup Dear PyGui
            dpg.setup_dearpygui()
            
            # Initialize renderer (lazy init after viewport is shown)
            self.renderer = None
            if MODERNGL_AVAILABLE:
                try:
                    self.renderer = ShaderRenderer(
                        width=DEFAULT_RENDER_WIDTH, 
                        height=DEFAULT_RENDER_HEIGHT
                    )
                except Exception as e:
                    print(f"Failed to create GPU renderer: {e}")
                    self.renderer = None
            
            # Initialize texture and rendering state
            self._initialize_rendering_state()
            
            # Initialize performance tracking
            self._initialize_performance_tracking()
            
            # Initialize rendering mode flags
            self.use_gpu = MODERNGL_AVAILABLE and self.renderer is not None
            self._gpu_failed_once = False
            self._last_render_time = 0.0
            self._render_cache_valid = False
            self._last_color_state = None
            
            # Initialize UI state
            self._toast_id = None
            self._toast_expire = 0.0
            
            # Create user interface
            self._create_ui()
            
            print("Initialization complete!")
            
        except Exception as e:
            print(f"Application initialization failed: {e}")
            # Cleanup partial initialization
            self._cleanup_on_error()
            raise
    
    def _initialize_fonts(self):
        """Initialize fonts with proper error handling"""
        self.header_font = None
        try:
            with dpg.font_registry():
                # Try common bold fonts on various platforms
                candidate_paths = [
                    "/System/Library/Fonts/SFNS.ttf",  # older macOS
                    "/System/Library/Fonts/SFNSDisplay.ttf",  # macOS
                    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
                    "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",  # macOS
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                    "C:\\Windows\\Fonts\\arialbd.ttf",  # Windows
                ]
                
                for font_path in candidate_paths:
                    try:
                        if os.path.exists(font_path):
                            self.header_font = dpg.add_font(font_path, 18)
                            print(f"Loaded header font: {font_path}")
                            break
                    except Exception as e:
                        print(f"Failed to load font {font_path}: {e}")
                        continue
                
                # Fallback: larger default font if none found
                if self.header_font is None:
                    self.header_font = dpg.add_font_default(size=18)
                    print("Using default font for headers")
                    
        except Exception as e:
            print(f"Font initialization failed: {e}")
            # Continue without custom fonts
            self.header_font = None
    
    def _setup_theme(self):
        """Setup the modern dark theme"""
        try:
            with dpg.theme() as global_theme:
                with dpg.theme_component(dpg.mvAll):
                    # Modern dark colors with translucency (glass-like)
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (15, 15, 20, 220))
                    dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 25, 30, 180))
                    dpg.add_theme_color(dpg.mvThemeCol_Border, (70, 70, 80, 140))
                    dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (35, 35, 45, 170))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (45, 45, 60, 200))
                    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (60, 60, 80, 220))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (20, 20, 25, 220))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (25, 25, 30, 230))
                    dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (15, 15, 20, 210))
                    dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 80, 170))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 110, 200))
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 130, 230))
                    dpg.add_theme_color(dpg.mvThemeCol_Header, (40, 40, 60, 170))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (55, 55, 80, 200))
                    dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (70, 70, 100, 220))
                    dpg.add_theme_color(dpg.mvThemeCol_Separator, (80, 80, 95, 150))
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorHovered, (100, 100, 120, 180))
                    dpg.add_theme_color(dpg.mvThemeCol_SeparatorActive, (130, 130, 160, 200))
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGrip, (60, 60, 80, 150))
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGripHovered, (80, 80, 110, 180))
                    dpg.add_theme_color(dpg.mvThemeCol_ResizeGripActive, (100, 100, 130, 200))
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (15, 15, 20, 0))
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (60, 60, 80, 150))
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (80, 80, 110, 180))
                    dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (100, 100, 130, 200))
                    
                    # Text colors
                    dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
                    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (220, 220, 220, 200))
                    dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (120, 120, 160, 120))
                    
                    # Slider colors
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (130, 130, 200, 220))
                    dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (160, 160, 220, 240))
                    
                    # Style settings
                    dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 16)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 14)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 8)
                    dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 12)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
                    dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 8)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 8, 6)
            
            dpg.bind_theme(global_theme)
            print("Theme applied successfully")
            
        except Exception as e:
            print(f"Theme setup failed: {e}")
            # Continue with default theme
    
    def _initialize_rendering_state(self):
        """Initialize texture and rendering state"""
        try:
            # Set render dimensions
            self.width = DEFAULT_RENDER_WIDTH
            self.height = DEFAULT_RENDER_HEIGHT
            
            # Create texture registry
            with dpg.texture_registry():
                # Initialize with black texture
                self.texture_data = np.zeros((self.height, self.width, 4), dtype=np.float32)
                self.texture_id = dpg.add_dynamic_texture(self.width, self.height, self.texture_data)
                
            print("Rendering state initialized")
            
        except Exception as e:
            print(f"Failed to initialize rendering state: {e}")
            raise RuntimeError(f"Rendering initialization failed: {e}") from e
    
    def _initialize_performance_tracking(self):
        """Initialize performance tracking variables"""
        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0.0
        self.frame_times = np.zeros(FRAME_TIME_SAMPLES, dtype=np.float32)
        self.frame_time_idx = 0
        
        # Adaptive rendering settings
        self.target_frame_time = 1.0 / TARGET_FPS
        self.skip_frames = 0
        self.ray_quality = 0
        self.last_quality_check = time.time()
        
        print("Performance tracking initialized")
    
    def _cleanup_on_error(self):
        """Clean up resources when initialization fails"""
        try:
            if hasattr(self, 'renderer') and self.renderer:
                self.renderer.cleanup()
        except Exception:
            pass
        
        try:
            dpg.destroy_context()
        except Exception:
            pass
    
    def _has_color_state_changed(self) -> bool:
        """Check if the color state has changed since last render"""
        current_state = (
            self.color_engine.hue,
            self.color_engine.saturation, 
            self.color_engine.brightness,
            self.color_engine.fluorescence,
            self.color_engine.neon_mode,
            self.color_engine.halo_width,
            self.color_engine.halo_intensity
        )
        
        if self._last_color_state != current_state:
            self._last_color_state = current_state
            return True
        return False
    
    def _create_ui(self):
        """Create the user interface"""
        # Main window
        with dpg.window(label="Neon & Anti-Neon Demo", no_close=True, tag="main_window"):
            dpg.set_primary_window("main_window", True)
            
            # Two-panel layout
            with dpg.group(horizontal=True):
                # Left panel - Rendering
                with dpg.child_window(width=RENDER_PANEL_WIDTH, height=DEFAULT_RENDER_HEIGHT, tag="render_panel"):
                    dpg.add_image(self.texture_id, width=RENDER_PANEL_WIDTH, height=DEFAULT_RENDER_HEIGHT)
                
                # Right panel - Controls
                with dpg.child_window(width=CONTROL_PANEL_WIDTH, height=DEFAULT_RENDER_HEIGHT, tag="control_panel"):
                    dpg.add_text("Color Settings", color=[255, 255, 255], tag="hdr_color_settings")
                    if self.header_font:
                        dpg.bind_item_font("hdr_color_settings", self.header_font)
                    dpg.add_separator()
                    
                    # Mode toggle
                    with dpg.group(horizontal=True):
                        dpg.add_text("Mode:")
                        dpg.add_radio_button(
                            items=["Neon", "Anti-Neon"],
                            default_value="Neon",
                            callback=self._on_mode_change,
                            horizontal=True
                        )
                    
                    dpg.add_spacer(height=10)
                    
                    # Hue slider
                    dpg.add_text("Hue")
                    dpg.add_slider_float(
                        label="",
                        default_value=0,
                        min_value=0,
                        max_value=360,
                        callback=self._on_hue_change,
                        width=SLIDER_WIDTH,
                        tag="hue_slider"
                    )
                    
                    # Saturation slider
                    dpg.add_text("Saturation")
                    dpg.add_slider_float(
                        label="",
                        default_value=1.0,
                        min_value=0.0,
                        max_value=1.0,
                        callback=self._on_saturation_change,
                        width=SLIDER_WIDTH,
                        tag="saturation_slider"
                    )
                    
                    # Brightness slider
                    dpg.add_text("Brightness")
                    dpg.add_slider_float(
                        label="",
                        default_value=1.0,
                        min_value=0.0,
                        max_value=1.0,
                        callback=self._on_brightness_change,
                        width=SLIDER_WIDTH,
                        tag="brightness_slider"
                    )
                    
                    # Fluorescence slider
                    dpg.add_text("Fluorescence")
                    dpg.add_slider_float(
                        label="",
                        default_value=0.5,
                        min_value=0.0,
                        max_value=1.0,
                        callback=self._on_fluorescence_change,
                        width=SLIDER_WIDTH,
                        tag="fluorescence_slider"
                    )
                    
                    dpg.add_spacer(height=20)
                    
                    # Preset buttons
                    dpg.add_text("Quick Presets", color=[255, 255, 255], tag="hdr_quick_presets")
                    if self.header_font:
                        dpg.bind_item_font("hdr_quick_presets", self.header_font)
                    dpg.add_separator()
                    
                    # Halo controls (for neon look and neon-brown)
                    dpg.add_text("Halo Width")
                    dpg.add_slider_float(
                        default_value=self.color_engine.halo_width,
                        min_value=0.02,
                        max_value=0.4,
                        width=SLIDER_WIDTH,
                        callback=self._on_halo_width_change,
                        tag="halo_width_slider"
                    )
                    dpg.add_text("Halo Intensity")
                    dpg.add_slider_float(
                        default_value=self.color_engine.halo_intensity,
                        min_value=0.0,
                        max_value=2.0,
                        width=SLIDER_WIDTH,
                        callback=self._on_halo_intensity_change,
                        tag="halo_intensity_slider"
                    )
                    
                    dpg.add_spacer(height=10)
                    
                    # Rendering mode toggle
                    with dpg.group(horizontal=True):
                        dpg.add_text("Renderer:")
                        dpg.add_radio_button(
                            items=["GPU", "CPU"],
                            default_value="GPU",
                            callback=self._on_renderer_toggle,
                            tag="renderer_mode"
                        )
                    
                    dpg.add_spacer(height=10)
                    
                    # Create preset buttons in a grid layout
                    preset_names = ["Classic Neon", "Cool Blue", "Warm Orange", "Electric Green", 
                                  "Vaporwave Pink", "Cyberpunk Red", "Anti-Neon Cool", "Anti-Neon Warm", "Neon Brown"]
                    
                    for i in range(0, len(preset_names), 2):
                        with dpg.group(horizontal=True):
                            for j in range(2):
                                if i + j < len(preset_names):
                                    preset_name = preset_names[i + j]
                                    dpg.add_button(
                                        label=preset_name,
                                        width=PRESET_BUTTON_WIDTH,
                                        callback=lambda s, a, u: self._on_preset_select(u),
                                        user_data=preset_name,
                                        tag=f"preset_{preset_name.lower().replace(' ', '_')}"
                                    )
                    
                    dpg.add_spacer(height=20)
                    
                    # Reset Button
                    dpg.add_button(label="Reset", callback=self._on_reset)
                    
                    dpg.add_spacer(height=10)
                    
                    # Export Button
                    dpg.add_button(
                        label="Export Image",
                        width=SLIDER_WIDTH,
                        callback=self._on_export_image,
                        tag="export_button"
                    )
                    
                    dpg.add_spacer(height=20)
            
            # Bottom info panel across the width
            with dpg.child_window(width=INFO_PANEL_WIDTH, height=INFO_PANEL_HEIGHT, tag="info_panel"):
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text("System & Renderer", color=[255, 255, 255], tag="hdr_system_renderer")
                        if self.header_font:
                            dpg.bind_item_font("hdr_system_renderer", self.header_font)
                        dpg.add_separator()
                        dpg.add_text("FPS: 0", tag="fps_text")
                        dpg.add_text("Renderer: GPU", tag="renderer_text")
                        dpg.add_text("Current Mode: Neon", tag="mode_text")
                    with dpg.group():
                        dpg.add_text("Color State", color=[255, 255, 255], tag="hdr_color_state")
                        if self.header_font:
                            dpg.bind_item_font("hdr_color_state", self.header_font)
                        dpg.add_separator()
                        dpg.add_text("Hue: 0.0", tag="hue_text")
                        dpg.add_text("Saturation: 1.0", tag="saturation_text")
                        dpg.add_text("Brightness: 1.0", tag="brightness_text")
                        dpg.add_text("Fluorescence: 0.5", tag="fluorescence_text")
    
    def _on_hue_change(self, sender, app_data):
        """Handle hue change"""
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_hue=app_data, duration=0.3)
        else:
            self.color_engine.set_hue(app_data)
        dpg.set_value("hue_text", f"Hue: {app_data:.1f}")
        self._render_cache_valid = False
    
    def _on_saturation_change(self, sender, app_data):
        """Handle saturation change"""
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_saturation=app_data, duration=0.3)
        else:
            self.color_engine.set_saturation(app_data)
        dpg.set_value("saturation_text", f"Saturation: {app_data:.2f}")
        self._render_cache_valid = False
    
    def _on_brightness_change(self, sender, app_data):
        """Handle brightness change"""
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_brightness=app_data, duration=0.3)
        else:
            self.color_engine.set_brightness(app_data)
        dpg.set_value("brightness_text", f"Brightness: {app_data:.2f}")
        self._render_cache_valid = False
    
    def _on_fluorescence_change(self, sender, app_data):
        """Handle fluorescence change"""
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_fluorescence=app_data, duration=0.3)
        else:
            self.color_engine.set_fluorescence(app_data)
        dpg.set_value("fluorescence_text", f"Fluorescence: {app_data:.2f}")
        self._render_cache_valid = False
    
    def _on_halo_width_change(self, sender, app_data):
        """Handle halo width change"""
        if hasattr(self.color_engine, 'set_halo_width'):
            self.color_engine.set_halo_width(app_data)
        self._render_cache_valid = False
    
    def _on_halo_intensity_change(self, sender, app_data):
        """Handle halo intensity change"""
        if hasattr(self.color_engine, 'set_halo_intensity'):
            self.color_engine.set_halo_intensity(app_data)
        self._render_cache_valid = False
    
    def _on_renderer_toggle(self, sender, app_data):
        """Handle renderer mode toggle between GPU and CPU"""
        self.use_gpu = (app_data == "GPU")
        if dpg.does_item_exist("renderer_text"):
            dpg.set_value("renderer_text", f"Renderer: {'GPU' if self.use_gpu else 'CPU'}")
    
    def _on_mode_change(self, sender, app_data):
        """Handle mode toggle"""
        neon_mode = app_data == "Neon"
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_neon_mode=neon_mode, duration=0.5)
        else:
            self.color_engine.set_neon_mode(neon_mode)
        dpg.set_value("mode_text", f"Current Mode: {app_data}")
        self._render_cache_valid = False
    
    def _on_preset_select(self, preset_name):
        """Handle preset button click"""
        if hasattr(self.color_engine, 'apply_preset'):
            success = self.color_engine.apply_preset(preset_name, duration=1.0)
            if success:
                print(f"Applied preset: {preset_name}")
                # Sync UI hints (texts)
                if dpg.does_item_exist("mode_text"):
                    dpg.set_value("mode_text", f"Current Mode: {'Neon' if self.color_engine.neon_mode else 'Anti-Neon'}")
                self._render_cache_valid = False
            else:
                print(f"Failed to apply preset: {preset_name}")
                self._show_toast(f"Failed to apply preset: {preset_name}", 2.0)
    
    def _on_export_image(self):
        """Export current rendering as PNG image with improved error handling"""
        try:
            # Validate that we have image data
            if self.texture_data is None:
                error_msg = "No image data to export yet. Please wait for rendering to complete."
                print(error_msg)
                self._show_toast(error_msg)
                return
            
            # Create exports directory with proper error handling
            export_dir = DEFAULT_EXPORT_DIR
            try:
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir, mode=0o755)
            except OSError as e:
                error_msg = f"Cannot create export directory '{export_dir}': {e}"
                print(error_msg)
                self._show_toast(error_msg)
                return
            
            # Generate safe filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neon_demo_{timestamp}.png"
            filepath = os.path.join(export_dir, filename)
            
            # Validate export data
            pixel_data = self.texture_data
            if pixel_data.size == 0 or pixel_data.dtype != np.float32:
                error_msg = "Invalid image data format for export."
                print(error_msg)
                self._show_toast(error_msg)
                return
            
            # Convert float32 RGBA (0-1) to uint8 (0-255) with proper clamping
            img_uint8 = np.clip(pixel_data * 255.0, 0, 255).astype(np.uint8)
            
            # Flip vertically for standard image coordinate system
            img_uint8 = np.flipud(img_uint8)
            
            # Save PNG via Pillow with error handling
            try:
                image = Image.fromarray(img_uint8, mode='RGBA')
                image.save(filepath, format=EXPORT_IMAGE_FORMAT, optimize=True)
                
                # Verify file was written successfully
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    msg = f"Image exported successfully to {filename}"
                    print(msg)
                    self._show_toast(msg)
                else:
                    error_msg = "Export completed but file verification failed."
                    print(error_msg)
                    self._show_toast(error_msg)
                    
            except Exception as e:
                error_msg = f"Failed to save image: {e}"
                print(error_msg)
                self._show_toast(error_msg)
                
        except Exception as e:
            error_msg = f"Export failed with unexpected error: {e}"
            print(error_msg)
            self._show_toast(error_msg)
    
    def _show_toast(self, message: str, duration: float = 2.5):
        """Show a temporary toast notification in the top-right corner."""
        # Delete existing toast if present
        try:
            if self._toast_id and dpg.does_item_exist(self._toast_id):
                dpg.delete_item(self._toast_id)
        except Exception:
            pass
        
        # Compute position near top-right of the viewport
        try:
            vp_w = dpg.get_viewport_client_width()
            vp_h = dpg.get_viewport_client_height()
        except Exception:
            vp_w, vp_h = 1200, 800
        width = 420
        height = 60
        pos_x = max(10, vp_w - width - 20)
        pos_y = 20
        
        with dpg.window(no_title_bar=True, no_move=True, no_resize=True, no_collapse=True,
                        autosize=False, width=width, height=height, pos=[pos_x, pos_y],
                        no_close=True, tag=f"toast_{int(time.time()*1000)}") as win_id:
            dpg.add_text(message, color=[255, 255, 255])
        self._toast_id = win_id
        self._toast_expire = time.time() + duration
    
    def _on_reset(self):
        """Handle reset button"""
        # Reset color engine to defaults with animation
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(
                target_hue=0.0,
                target_saturation=1.0,
                target_brightness=1.0,
                target_fluorescence=0.5,
                target_neon_mode=True,
                duration=0.5
            )
        else:
            # Fallback to instant reset
            self.color_engine.set_hue(0.0)
            self.color_engine.set_saturation(1.0)
            self.color_engine.set_brightness(1.0)
            self.color_engine.set_fluorescence(0.5)
            self.color_engine.set_neon_mode(True)
        
        # Reset UI controls (texts and sliders)
        if dpg.does_item_exist("hue_text"):
            dpg.set_value("hue_text", "Hue: 0.0")
        if dpg.does_item_exist("saturation_text"):
            dpg.set_value("saturation_text", "Saturation: 1.0")
        if dpg.does_item_exist("brightness_text"):
            dpg.set_value("brightness_text", "Brightness: 1.0")
        if dpg.does_item_exist("fluorescence_text"):
            dpg.set_value("fluorescence_text", "Fluorescence: 0.5")
        if dpg.does_item_exist("mode_text"):
            dpg.set_value("mode_text", "Current Mode: Neon")
        # Sliders
        for tag, val in [("hue_slider", 0.0), ("saturation_slider", 1.0), ("brightness_slider", 1.0), ("fluorescence_slider", 0.5), ("halo_width_slider", self.color_engine.halo_width), ("halo_intensity_slider", self.color_engine.halo_intensity)]:
            if dpg.does_item_exist(tag):
                dpg.set_value(tag, val)
        # Renderer toggle back to GPU (will fallback if needed)
        if dpg.does_item_exist("renderer_mode"):
            dpg.set_value("renderer_mode", "GPU")
        if dpg.does_item_exist("renderer_text"):
            dpg.set_value("renderer_text", "Renderer: GPU")
        
        # Invalidate render cache
        self._render_cache_valid = False
    
    def _calculate_fps(self):
        """Calculate frames per second with improved performance monitoring"""
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        # Store frame time in circular buffer for averaging
        self.frame_times[self.frame_time_idx] = elapsed
        self.frame_time_idx = (self.frame_time_idx + 1) % len(self.frame_times)
        
        # Calculate FPS based on average of recent frame times
        valid_times = self.frame_times[self.frame_times > 0]
        if len(valid_times) > 0:
            avg_frame_time = np.mean(valid_times)
            self.fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        # Update FPS counter periodically for smoother display
        self.frame_count += 1
        if self.frame_count >= FPS_UPDATE_INTERVAL:
            # Update FPS display
            if dpg.does_item_exist("fps_text"):
                dpg.set_value("fps_text", f"FPS: {self.fps:.1f}")
                
                # Adjust rendering quality based on performance
                if self.fps < LOW_FPS_THRESHOLD and self.skip_frames < MAX_FRAME_SKIP:
                    self.skip_frames += 1
                    if self.color_engine.neon_mode and self.ray_quality > 0:
                        self.ray_quality -= 1
                        
                elif self.fps > GOOD_FPS_THRESHOLD and self.skip_frames > 0:
                    self.skip_frames -= 1
                    
                    # Gradually increase ray quality if possible
                    if current_time - self.last_quality_check > 2.0:
                        if self.ray_quality < 2:
                            self.ray_quality += 1
                        self.last_quality_check = current_time
            
            self.frame_count = 0
            
        self.last_time = current_time
    
    def _render_frame(self):
        """Render a frame using GPU shaders if available, else CPU fallback
        
        Optimized to skip rendering when color state hasn't changed and no animations are running.
        """
        try:
            # Update animations and demo mode
            if hasattr(self.color_engine, 'update_animation'):
                self.color_engine.update_animation()
            if hasattr(self.color_engine, 'update_demo'):
                self.color_engine.update_demo()
            
            # Performance optimization: skip render if nothing changed
            current_time = time.time()
            has_changed = self._has_color_state_changed()
            is_animating = getattr(self.color_engine, 'is_animating', False)
            
            # Only render if something changed, animating, or enough time passed for demo mode
            time_since_render = current_time - self._last_render_time
            should_render = (has_changed or is_animating or 
                           (hasattr(self.color_engine, 'demo_mode') and 
                            self.color_engine.demo_mode and time_since_render > 0.033))  # ~30fps for demo
            
            if not should_render and self._render_cache_valid:
                self._handle_toast_expiration()
                return
            
            # Try GPU rendering if enabled and available
            if self.use_gpu and self.renderer:
                try:
                    self.texture_data = self.renderer.render_frame(self.color_engine)
                    dpg.set_value(self.texture_id, self.texture_data)
                    self._render_cache_valid = True
                    self._last_render_time = current_time
                    self._handle_toast_expiration()
                    return
                    
                except Exception as e:
                    # Disable GPU after first failure to avoid log spam
                    if not self._gpu_failed_once:
                        print(f"GPU render failed, switching to CPU: {e}")
                        self._gpu_failed_once = True
                        self._show_toast("GPU rendering failed, switched to CPU mode", 3.0)
                    
                    self.use_gpu = False
                    self._update_renderer_ui_status("CPU")
            
            # CPU fallback rendering
            self._fallback_render()
            self._render_cache_valid = True
            self._last_render_time = current_time
            self._handle_toast_expiration()
            
        except Exception as e:
            print(f"Frame rendering failed: {e}")
            # Continue with black screen rather than crashing
            if hasattr(self, 'texture_data') and self.texture_data is not None:
                self.texture_data.fill(0)
                dpg.set_value(self.texture_id, self.texture_data)
                self._render_cache_valid = False
    
    def _update_renderer_ui_status(self, mode):
        """Update UI to reflect current rendering mode"""
        try:
            if dpg.does_item_exist("renderer_text"):
                dpg.set_value("renderer_text", f"Renderer: {mode}")
            if dpg.does_item_exist("renderer_mode"):
                dpg.set_value("renderer_mode", mode)
        except Exception as e:
            print(f"Failed to update renderer UI status: {e}")
    
    def _handle_toast_expiration(self):
        """Handle toast notification expiration"""
        if self._toast_id and time.time() > self._toast_expire:
            try:
                if dpg.does_item_exist(self._toast_id):
                    dpg.delete_item(self._toast_id)
            except Exception:
                pass
            self._toast_id = None
    
    def _fallback_render(self):
        """Enhanced CPU-based fallback rendering with better error handling"""
        try:
            r, g, b = self.color_engine.get_rgb()
            
            # Validate color values
            if not all(0 <= val <= 1 for val in [r, g, b]):
                print(f"Warning: Invalid color values: r={r}, g={g}, b={b}")
                r, g, b = max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b))
            
            # Create circular gradient effect
            center_x, center_y = self.width // 2, self.height // 2
            y_coords, x_coords = np.ogrid[:self.height, :self.width]
            
            # Calculate distances from center
            distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
            
            # Create circular gradient with proper normalization
            max_dist = min(center_x, center_y) * 0.8  # Leave some border
            intensity = np.clip(1.0 - distances / max_dist, 0, 1.0)
            
            # Apply different effects based on mode
            if self.color_engine.neon_mode:
                # Neon mode: bright center with glow effect
                intensity = intensity ** 0.7  # Softer falloff
                brightness_multiplier = 1.0 + self.color_engine.fluorescence * 0.5
            else:
                # Anti-neon mode: darker, more muted
                intensity = intensity ** 1.5  # Sharper falloff
                brightness_multiplier = 0.6
                r, g, b = r * 0.7, g * 0.7, b * 0.7  # Desaturate
            
            # Apply final intensity and brightness
            final_intensity = intensity * brightness_multiplier
            
            # Update texture data
            self.texture_data[..., 0] = r * final_intensity
            self.texture_data[..., 1] = g * final_intensity  
            self.texture_data[..., 2] = b * final_intensity
            self.texture_data[..., 3] = final_intensity  # Alpha channel
            
            # Update texture
            dpg.set_value(self.texture_id, self.texture_data)
            
        except Exception as e:
            print(f"CPU fallback render failed: {e}")
            # Fill with solid color as last resort
            try:
                r, g, b = self.color_engine.get_rgb()
                self.texture_data.fill(0)
                self.texture_data[..., 0] = r * 0.5
                self.texture_data[..., 1] = g * 0.5
                self.texture_data[..., 2] = b * 0.5
                self.texture_data[..., 3] = 0.5
                dpg.set_value(self.texture_id, self.texture_data)
            except Exception:
                # Ultimate fallback: black screen
                if hasattr(self, 'texture_data') and self.texture_data is not None:
                    self.texture_data.fill(0)
                    dpg.set_value(self.texture_id, self.texture_data)
    
    def run(self):
        """Run the application"""
        print("Use the sliders to adjust colors & parameters.")
        print("Toggle between Neon & Anti-Neon modes.")
        print("Press ESC or close the window to exit.")
        
        # Show viewport
        dpg.show_viewport()
        
        # Warm up one Dear PyGui frame to ensure OpenGL context is current
        # before creating ModernGL resources
        try:
            dpg.render_dearpygui_frame()
            if self.use_gpu and hasattr(self, 'renderer') and hasattr(self.renderer, '_ensure_context'):
                # Try to initialize GL context/resources once
                self.renderer._ensure_context()
        except Exception as e:
            # If GPU init fails here, we'll fallback automatically in _render_frame
            print(f"GPU warmup skipped: {e}")
        
        # Frame timing variables
        frame_skip_counter = 0
        last_render_time = time.time()
        
        # Main loop
        while dpg.is_dearpygui_running():
            # Calculate time since last frame
            current_time = time.time()
            delta_time = current_time - last_render_time
            
            # Adaptive rendering - skip frames if needed to maintain performance
            if frame_skip_counter >= self.skip_frames:
                # Render frame
                self._render_frame()
                
                # Calculate FPS
                self._calculate_fps()
                
                # Reset frame skip counter
                frame_skip_counter = 0
                last_render_time = current_time
            else:
                # Skip this frame
                frame_skip_counter += 1
            
            # Render Dear PyGui frame (UI updates always happen)
            dpg.render_dearpygui_frame()
            
            # Small sleep to prevent CPU hogging when running very fast
            if delta_time < (1.0 / HIGH_FPS_THRESHOLD):
                time.sleep(CPU_THROTTLE_SLEEP)
        
        # Clean up
        dpg.destroy_context()
        if hasattr(self, 'renderer'):
            self.renderer.cleanup()
        print("Neon & Anti-Neon Demo closed.")


if __name__ == "__main__":
    app = NeonApp()
    app.run()
