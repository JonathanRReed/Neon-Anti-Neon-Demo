"""
Neon & Anti-Neon Demo - Color Perception Laboratory
Main application that integrates all components including illusion modules
"""

import numpy as np
import dearpygui.dearpygui as dpg
import time
import os
import sys
from datetime import datetime
from PIL import Image

from color_engine import ColorEngine
from color_management import ColorManagement, srgb_to_linear, linear_to_srgb
from validation_tools import EyedropperTool, CalibrationChecker

# Import illusion modules
from modules.neon_brown import NeonBrownModule
from modules.contrast_illusions import (
    SimultaneousContrastModule, CheckerShadowModule, 
    CornsweetModule, NeonSpreadingModule
)
from modules.chimerical import ChimericalModule, ChimericalType, CHIMERICAL_PRESETS
from modules.motion_illusions import LilacChaserModule, BenhamDiskModule

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

# Module Constants - Available illusion modules
AVAILABLE_MODULES = [
    ("Neon Demo", "neon_demo"),
    ("Neon Brown", "neon_brown"),
    ("Simultaneous Contrast", "simultaneous_contrast"),
    ("Checker Shadow", "checker_shadow"),
    ("Cornsweet Edge", "cornsweet"),
    ("Neon Spreading", "neon_spreading"),
    ("Chimerical Colors", "chimerical"),
    ("Lilac Chaser", "lilac_chaser"),
    ("Benham's Disk", "benham_disk"),
]

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
                # Pass time for pulsing animation
                if 'time' in program:
                    program['time'] = float(time.time() % 1000.0)  # Modulo to prevent precision issues
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
            
            # Initialize illusion modules
            self._initialize_illusion_modules()
            
            # Current active module
            self.current_module = "neon_demo"
            self.show_calibration = False
            
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
                # Initialize with black texture (DearPyGui expects flattened 1D array)
                # Create as 3D array then flatten for proper RGBA layout
                image = np.zeros((self.height, self.width, 4), dtype=np.float32)
                image[..., 3] = 1.0  # Full alpha
                self.texture_data = image.flatten()
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
    
    def _initialize_illusion_modules(self):
        """Initialize all illusion modules"""
        print("Initializing illusion modules...")
        
        # Create module instances
        self.modules = {
            "neon_brown": NeonBrownModule(),
            "simultaneous_contrast": SimultaneousContrastModule(),
            "checker_shadow": CheckerShadowModule(),
            "cornsweet": CornsweetModule(),
            "neon_spreading": NeonSpreadingModule(),
            "chimerical": ChimericalModule(),
            "lilac_chaser": LilacChaserModule(),
            "benham_disk": BenhamDiskModule(),
        }
        
        # Initialize validation tools
        self.eyedropper = EyedropperTool()
        
        # Module-specific state
        self._module_texture_data = None
        self._module_needs_update = True
        
        print(f"Initialized {len(self.modules)} illusion modules")
    
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
        with dpg.window(label="Color Perception Laboratory", no_close=True, tag="main_window"):
            dpg.set_primary_window("main_window", True)
            
            # Top bar with module selector
            with dpg.child_window(width=-1, height=45, tag="module_bar"):
                with dpg.group(horizontal=True):
                    dpg.add_text("Module:", color=[200, 200, 255])
                    dpg.add_combo(
                        items=[name for name, _ in AVAILABLE_MODULES],
                        default_value="Neon Demo",
                        callback=self._on_module_change,
                        width=200,
                        tag="module_selector"
                    )
                    dpg.add_spacer(width=20)
                    dpg.add_button(
                        label="Calibration",
                        callback=self._on_calibration_toggle,
                        tag="calibration_button"
                    )
                    dpg.add_spacer(width=20)
                    dpg.add_text("", tag="module_info_text", color=[150, 200, 150])
            
            dpg.add_spacer(height=5)
            
            # Two-panel layout
            with dpg.group(horizontal=True):
                # Left panel - Rendering
                with dpg.child_window(width=RENDER_PANEL_WIDTH, height=DEFAULT_RENDER_HEIGHT, tag="render_panel"):
                    dpg.add_image(self.texture_id, width=RENDER_PANEL_WIDTH, height=DEFAULT_RENDER_HEIGHT, tag="render_image")
                
                # Right panel - Controls (will be different for each module)
                with dpg.child_window(width=CONTROL_PANEL_WIDTH, height=DEFAULT_RENDER_HEIGHT, tag="control_panel"):
                    # Neon Demo controls (shown by default) - ALL controls in one group
                    with dpg.group(tag="neon_demo_controls"):
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
                                horizontal=True,
                                tag="mode_radio"
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
                        
                        # Create preset buttons in a grid layout - now with all 13 presets
                        preset_names = ColorEngine.get_preset_names()
                        
                        # Use 3-column layout for more presets
                        for i in range(0, len(preset_names), 3):
                            with dpg.group(horizontal=True):
                                for j in range(3):
                                    if i + j < len(preset_names):
                                        preset_name = preset_names[i + j]
                                        dpg.add_button(
                                            label=preset_name,
                                            width=PRESET_BUTTON_WIDTH,
                                            callback=lambda s, a, u: self._on_preset_select(u),
                                            user_data=preset_name,
                                            tag=f"preset_{preset_name.lower().replace(' ', '_').replace('-', '_')}"
                                        )
                        
                        dpg.add_spacer(height=15)
                        
                        # Fun action buttons
                        dpg.add_text("Actions", color=[255, 255, 255], tag="hdr_actions")
                        if self.header_font:
                            dpg.bind_item_font("hdr_actions", self.header_font)
                        dpg.add_separator()
                        
                        with dpg.group(horizontal=True):
                            dpg.add_button(
                                label="🎲 Random",
                                width=PRESET_BUTTON_WIDTH,
                                callback=self._on_random_color,
                                tag="random_button"
                            )
                            dpg.add_button(
                                label="▶ Demo",
                                width=PRESET_BUTTON_WIDTH,
                                callback=self._on_demo_toggle,
                                tag="demo_button"
                            )
                            dpg.add_button(
                                label="Reset",
                                width=PRESET_BUTTON_WIDTH,
                                callback=self._on_reset,
                                tag="reset_button"
                            )
                        
                        dpg.add_spacer(height=10)
                        
                        # Export Button
                        dpg.add_button(
                            label="📷 Export Image",
                            width=SLIDER_WIDTH,
                            callback=self._on_export_image,
                            tag="export_button"
                        )
                        
                        dpg.add_spacer(height=10)
                        
                        # Keyboard shortcuts help
                        dpg.add_text("Shortcuts: Space=Mode, R=Reset, ←→=Hue", 
                                    color=[150, 150, 160], tag="shortcuts_help")
                    
                    # END of neon_demo_controls group
                    
                    # Module-specific control panels (hidden by default)
                    self._create_module_controls()
            
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
                    
                    dpg.add_spacer(width=40)
                    
                    with dpg.group():
                        dpg.add_text("Color State", color=[255, 255, 255], tag="hdr_color_state")
                        if self.header_font:
                            dpg.bind_item_font("hdr_color_state", self.header_font)
                        dpg.add_separator()
                        dpg.add_text("Hue: 0.0°", tag="hue_text")
                        dpg.add_text("Saturation: 1.00", tag="saturation_text")
                        dpg.add_text("Brightness: 1.00", tag="brightness_text")
                        dpg.add_text("Fluorescence: 0.50", tag="fluorescence_text")
                    
                    dpg.add_spacer(width=40)
                    
                    with dpg.group():
                        dpg.add_text("Color Values", color=[255, 255, 255], tag="hdr_color_values")
                        if self.header_font:
                            dpg.bind_item_font("hdr_color_values", self.header_font)
                        dpg.add_separator()
                        dpg.add_text("HEX: #FF0000", tag="hex_text")
                        dpg.add_text("RGB: 255, 0, 0", tag="rgb_text")
        
        # Register keyboard handler
        with dpg.handler_registry():
            dpg.add_key_press_handler(callback=self._on_key_press)
    
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
                # Sync UI to reflect target preset values immediately
                self._sync_ui_with_engine(use_targets=True)
                self._render_cache_valid = False
            else:
                print(f"Failed to apply preset: {preset_name}")
                self._show_toast(f"Failed to apply preset: {preset_name}", 2.0)

    def _sync_ui_with_engine(self, use_targets: bool = False):
        """Synchronize UI controls and labels with the ColorEngine state.
        
        Args:
            use_targets: If True, use target_* values (useful right after starting an animation),
                         otherwise use current values.
        """
        try:
            ce = self.color_engine
            hue = getattr(ce, 'target_hue', ce.hue) if use_targets else ce.hue
            saturation = getattr(ce, 'target_saturation', ce.saturation) if use_targets else ce.saturation
            brightness = getattr(ce, 'target_brightness', ce.brightness) if use_targets else ce.brightness
            fluorescence = getattr(ce, 'target_fluorescence', ce.fluorescence) if use_targets else ce.fluorescence
            neon_mode = getattr(ce, 'target_neon_mode', ce.neon_mode) if use_targets else ce.neon_mode

            # Update text labels
            if dpg.does_item_exist("hue_text"):
                dpg.set_value("hue_text", f"Hue: {hue:.1f}")
            if dpg.does_item_exist("saturation_text"):
                dpg.set_value("saturation_text", f"Saturation: {saturation:.2f}")
            if dpg.does_item_exist("brightness_text"):
                dpg.set_value("brightness_text", f"Brightness: {brightness:.2f}")
            if dpg.does_item_exist("fluorescence_text"):
                dpg.set_value("fluorescence_text", f"Fluorescence: {fluorescence:.2f}")
            if dpg.does_item_exist("mode_text"):
                dpg.set_value("mode_text", f"Current Mode: {'Neon' if neon_mode else 'Anti-Neon'}")

            # Update sliders to reflect values
            if dpg.does_item_exist("hue_slider"):
                dpg.set_value("hue_slider", float(hue))
            if dpg.does_item_exist("saturation_slider"):
                dpg.set_value("saturation_slider", float(saturation))
            if dpg.does_item_exist("brightness_slider"):
                dpg.set_value("brightness_slider", float(brightness))
            if dpg.does_item_exist("fluorescence_slider"):
                dpg.set_value("fluorescence_slider", float(fluorescence))

            # Halo controls (no presets currently define these; use current values)
            if dpg.does_item_exist("halo_width_slider"):
                dpg.set_value("halo_width_slider", float(ce.halo_width))
            if dpg.does_item_exist("halo_intensity_slider"):
                dpg.set_value("halo_intensity_slider", float(ce.halo_intensity))

            # Update mode radio selection
            if dpg.does_item_exist("mode_radio"):
                dpg.set_value("mode_radio", "Neon" if neon_mode else "Anti-Neon")
            
            # Update HEX and RGB color displays
            hex_color = ce.get_hex_color()
            r, g, b = ce.get_rgb()
            if dpg.does_item_exist("hex_text"):
                dpg.set_value("hex_text", f"HEX: {hex_color.upper()}")
            if dpg.does_item_exist("rgb_text"):
                dpg.set_value("rgb_text", f"RGB: {int(r*255)}, {int(g*255)}, {int(b*255)}")
        except Exception as e:
            print(f"Failed to sync UI with engine: {e}")
    
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
        
        # Sync UI to the reset target values immediately
        self._sync_ui_with_engine(use_targets=True)
        # Renderer toggle back to GPU (will fallback if needed)
        if dpg.does_item_exist("renderer_mode"):
            dpg.set_value("renderer_mode", "GPU")
        if dpg.does_item_exist("renderer_text"):
            dpg.set_value("renderer_text", "Renderer: GPU")
        
        # Invalidate render cache
        self._render_cache_valid = False
    
    def _on_random_color(self):
        """Handle random color button"""
        if hasattr(self.color_engine, 'randomize_color'):
            self.color_engine.randomize_color(duration=0.5)
            self._sync_ui_with_engine(use_targets=True)
            self._render_cache_valid = False
    
    def _on_demo_toggle(self):
        """Handle demo mode toggle button"""
        if self.color_engine.demo_mode:
            self.color_engine.stop_demo_mode()
            if dpg.does_item_exist("demo_button"):
                dpg.set_item_label("demo_button", "▶ Demo")
            self._show_toast("Demo mode stopped", 1.5)
        else:
            self.color_engine.start_demo_mode()
            if dpg.does_item_exist("demo_button"):
                dpg.set_item_label("demo_button", "⏹ Stop")
            self._show_toast("Demo mode started - cycling through colors!", 2.0)
        self._render_cache_valid = False
    
    def _on_key_press(self, sender, app_data):
        """Handle keyboard shortcuts"""
        key = app_data
        
        # Space = Toggle Neon/Anti-Neon mode
        if key == dpg.mvKey_Spacebar:
            new_mode = not self.color_engine.neon_mode
            self.color_engine.animate_to(target_neon_mode=new_mode, duration=0.3)
            if dpg.does_item_exist("mode_radio"):
                dpg.set_value("mode_radio", "Neon" if new_mode else "Anti-Neon")
            self._sync_ui_with_engine(use_targets=True)
            self._render_cache_valid = False
        
        # R = Reset
        elif key == dpg.mvKey_R:
            self._on_reset()
        
        # Left Arrow = Decrease hue
        elif key == dpg.mvKey_Left:
            new_hue = (self.color_engine.hue - 15) % 360
            self.color_engine.animate_to(target_hue=new_hue, duration=0.2)
            self._sync_ui_with_engine(use_targets=True)
            self._render_cache_valid = False
        
        # Right Arrow = Increase hue
        elif key == dpg.mvKey_Right:
            new_hue = (self.color_engine.hue + 15) % 360
            self.color_engine.animate_to(target_hue=new_hue, duration=0.2)
            self._sync_ui_with_engine(use_targets=True)
            self._render_cache_valid = False
        
        # Up Arrow = Increase brightness
        elif key == dpg.mvKey_Up:
            new_brightness = min(1.0, self.color_engine.brightness + 0.1)
            self.color_engine.animate_to(target_brightness=new_brightness, duration=0.2)
            self._sync_ui_with_engine(use_targets=True)
            self._render_cache_valid = False
        
        # Down Arrow = Decrease brightness
        elif key == dpg.mvKey_Down:
            new_brightness = max(0.0, self.color_engine.brightness - 0.1)
            self.color_engine.animate_to(target_brightness=new_brightness, duration=0.2)
            self._sync_ui_with_engine(use_targets=True)
            self._render_cache_valid = False
        
        # D = Toggle demo mode
        elif key == dpg.mvKey_D:
            self._on_demo_toggle()
        
        # Number keys 1-9 for presets
        elif key >= dpg.mvKey_1 and key <= dpg.mvKey_9:
            preset_index = key - dpg.mvKey_1  # 0-8
            preset_names = ColorEngine.get_preset_names()
            if preset_index < len(preset_names):
                self._on_preset_select(preset_names[preset_index])
    
    def _create_module_controls(self):
        """Create control panels for each illusion module (hidden by default)"""
        
        # Generic module controls panel
        with dpg.group(tag="module_controls", show=False):
            dpg.add_text("Module Controls", color=[255, 255, 255], tag="hdr_module_controls")
            if self.header_font:
                dpg.bind_item_font("hdr_module_controls", self.header_font)
            dpg.add_separator()
            
            # Module description
            dpg.add_text("", tag="module_description", wrap=SLIDER_WIDTH, color=[180, 180, 200])
            
            dpg.add_spacer(height=10)
            
            # Pixel proof info
            dpg.add_text("Pixel Proof", color=[255, 200, 100], tag="hdr_pixel_proof")
            dpg.add_separator()
            dpg.add_text("", tag="proof_text", wrap=SLIDER_WIDTH, color=[150, 255, 150])
            
            dpg.add_spacer(height=15)
            
            # Module-specific sliders (will be populated when module is selected)
            with dpg.group(tag="module_sliders"):
                pass
            
            dpg.add_spacer(height=15)
            
            # Module actions
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔍 Show Proof",
                    callback=self._on_show_proof,
                    tag="show_proof_button",
                    width=PRESET_BUTTON_WIDTH
                )
                dpg.add_button(
                    label="ℹ️ Explanation",
                    callback=self._on_show_explanation,
                    tag="explanation_button",
                    width=PRESET_BUTTON_WIDTH
                )
            
            dpg.add_spacer(height=10)
            
            # Safety warning area (for modules that need it)
            with dpg.group(tag="safety_warning_group", show=False):
                dpg.add_text("[!] Safety Notice", color=[255, 200, 100])
                dpg.add_text("", tag="safety_warning_text", wrap=SLIDER_WIDTH, color=[255, 180, 180])
            
            dpg.add_spacer(height=10)
            
            # Animation controls (for modules with animation)
            with dpg.group(tag="animation_controls", show=False):
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="▶ Start",
                        callback=self._on_animation_start,
                        tag="animation_start_button",
                        width=PRESET_BUTTON_WIDTH
                    )
                    dpg.add_button(
                        label="⏹ Stop",
                        callback=self._on_animation_stop,
                        tag="animation_stop_button",
                        width=PRESET_BUTTON_WIDTH
                    )
    
    def _on_module_change(self, sender, app_data):
        """Handle module selection change"""
        # Find the module key from the display name
        module_key = "neon_demo"
        for name, key in AVAILABLE_MODULES:
            if name == app_data:
                module_key = key
                break
        
        self.current_module = module_key
        self._module_needs_update = True
        
        # Update UI visibility
        is_neon_demo = (module_key == "neon_demo")
        
        # Show/hide control panels
        if dpg.does_item_exist("neon_demo_controls"):
            dpg.configure_item("neon_demo_controls", show=is_neon_demo)
        if dpg.does_item_exist("module_controls"):
            dpg.configure_item("module_controls", show=not is_neon_demo)
        
        # Update module info
        if not is_neon_demo and module_key in self.modules:
            module = self.modules[module_key]
            
            # Update description
            if dpg.does_item_exist("module_description"):
                dpg.set_value("module_description", module.description)
            
            # Update proof text
            if hasattr(module, 'get_proof_info') and dpg.does_item_exist("proof_text"):
                dpg.set_value("proof_text", module.get_proof_info())
            
            # Update module info text
            if dpg.does_item_exist("module_info_text"):
                dpg.set_value("module_info_text", f"{module.name}")
            
            # Show safety warning if needed
            has_warning = hasattr(module, 'has_safety_warning') and module.has_safety_warning
            if dpg.does_item_exist("safety_warning_group"):
                dpg.configure_item("safety_warning_group", show=has_warning)
                if has_warning and hasattr(module, 'get_safety_warning'):
                    dpg.set_value("safety_warning_text", module.get_safety_warning())
            
            # Show animation controls for animated modules
            has_animation = hasattr(module, 'start') and hasattr(module, 'stop')
            if dpg.does_item_exist("animation_controls"):
                dpg.configure_item("animation_controls", show=has_animation)
        else:
            if dpg.does_item_exist("module_info_text"):
                dpg.set_value("module_info_text", "Original Neon Demo")
        
        # Force re-render
        self._render_cache_valid = False
    
    def _on_calibration_toggle(self):
        """Toggle calibration display"""
        self.show_calibration = not self.show_calibration
        
        if self.show_calibration:
            instructions = CalibrationChecker.get_calibration_instructions()
            self._show_toast("\n".join(instructions[:8]), 8.0)
        else:
            self._show_toast("Calibration closed", 1.0)
    
    def _on_show_proof(self):
        """Show pixel proof for current module"""
        if self.current_module in self.modules:
            module = self.modules[self.current_module]
            if hasattr(module, 'get_proof_info'):
                proof = module.get_proof_info()
                self._show_toast(proof, 5.0)
    
    def _on_show_explanation(self):
        """Show scientific explanation for current module"""
        if self.current_module in self.modules:
            module = self.modules[self.current_module]
            if hasattr(module, 'get_explanation'):
                explanation = module.get_explanation()
                self._show_toast(explanation[:500] + "...", 8.0)
            else:
                self._show_toast(module.description, 4.0)
    
    def _on_animation_start(self):
        """Start animation for current module"""
        if self.current_module in self.modules:
            module = self.modules[self.current_module]
            if hasattr(module, 'start'):
                module.start()
                self._module_needs_update = True
                self._show_toast("Animation started", 1.5)
    
    def _on_animation_stop(self):
        """Stop animation for current module"""
        if self.current_module in self.modules:
            module = self.modules[self.current_module]
            if hasattr(module, 'stop'):
                module.stop()
                self._show_toast("Animation stopped", 1.5)
    
    def _render_illusion_module(self):
        """Render the current illusion module to texture"""
        if self.current_module not in self.modules:
            return None
        
        module = self.modules[self.current_module]
        
        try:
            # Render the module
            image = module.render(DEFAULT_RENDER_WIDTH, DEFAULT_RENDER_HEIGHT)
            
            # Ensure proper format (float32, 0-1 range)
            if image.dtype != np.float32:
                image = image.astype(np.float32)
            
            # Add alpha channel if needed
            if image.shape[-1] == 3:
                alpha = np.ones((*image.shape[:2], 1), dtype=np.float32)
                image = np.concatenate([image, alpha], axis=-1)
            
            return image
            
        except Exception as e:
            print(f"Module render error: {e}")
            return None

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
        Now supports illusion module rendering.
        """
        try:
            # Check if rendering an illusion module
            if hasattr(self, 'current_module') and self.current_module != "neon_demo":
                self._render_module_frame()
                return
            
            # Update animations and demo mode (for neon demo)
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
            
            # Try GPU rendering if enabled and available with proper initialization
            gpu_success = False
            if self.use_gpu and self.renderer and hasattr(self.renderer, 'framebuffer') and self.renderer.framebuffer:
                try:
                    rendered = self.renderer.render_frame(self.color_engine)
                    # Flatten for DearPyGui (requires 1D array)
                    self.texture_data = rendered.flatten()
                    dpg.set_value(self.texture_id, self.texture_data)
                    self._render_cache_valid = True
                    self._last_render_time = current_time
                    self._handle_toast_expiration()
                    gpu_success = True
                    
                except Exception as e:
                    # Disable GPU after first failure to avoid log spam
                    if not self._gpu_failed_once:
                        print(f"GPU render failed, switching to CPU: {e}")
                        self._gpu_failed_once = True
                        self._show_toast("GPU rendering failed, switched to CPU mode", 3.0)
                    
                    self.use_gpu = False
                    self._update_renderer_ui_status("CPU")
            elif self.use_gpu and not self._gpu_failed_once:
                # GPU requested but not available - fail quietly once
                self._gpu_failed_once = True
                self.use_gpu = False
                self._update_renderer_ui_status("CPU")
            
            # CPU fallback rendering (if GPU didn't succeed)
            if not gpu_success:
                self._fallback_render()
                self._render_cache_valid = True
                self._last_render_time = current_time
                self._handle_toast_expiration()
            
        except Exception as e:
            # This should rarely happen now - final safety net
            if not hasattr(self, '_render_error_count'):
                self._render_error_count = 0
            self._render_error_count += 1
            if self._render_error_count <= 3:
                print(f"Frame rendering failed: {e}")
            # Try CPU fallback as last resort
            try:
                self._fallback_render()
            except Exception:
                pass  # Give up silently
    
    def _render_module_frame(self):
        """Render the current illusion module frame"""
        try:
            # Get the rendered image from the module
            image = self._render_illusion_module()
            
            if image is not None:
                # Flatten to 1D array for DearPyGui texture
                self.texture_data = image.flatten()
                dpg.set_value(self.texture_id, self.texture_data)
                
                # Update proof info periodically
                if hasattr(self, '_last_proof_update'):
                    if time.time() - self._last_proof_update > 1.0:
                        self._update_module_proof()
                        self._last_proof_update = time.time()
                else:
                    self._last_proof_update = time.time()
            
            self._handle_toast_expiration()
            
        except Exception as e:
            print(f"Module frame rendering failed: {e}")
    
    def _update_module_proof(self):
        """Update the proof text for the current module"""
        if self.current_module in self.modules:
            module = self.modules[self.current_module]
            if hasattr(module, 'get_proof_info') and dpg.does_item_exist("proof_text"):
                dpg.set_value("proof_text", module.get_proof_info())
    
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
            
            # Create RGBA image array
            image = np.zeros((self.height, self.width, 4), dtype=np.float32)
            image[..., 0] = r * final_intensity
            image[..., 1] = g * final_intensity  
            image[..., 2] = b * final_intensity
            image[..., 3] = np.clip(final_intensity, 0, 1)  # Alpha channel
            
            # Flatten for DearPyGui (requires 1D array)
            self.texture_data = image.flatten()
            
            # Update texture
            dpg.set_value(self.texture_id, self.texture_data)
            
        except Exception as e:
            print(f"CPU fallback render failed: {e}")
            # Fill with solid color as last resort
            try:
                r, g, b = self.color_engine.get_rgb()
                # Create simple solid color image
                image = np.zeros((self.height, self.width, 4), dtype=np.float32)
                image[..., 0] = r * 0.5
                image[..., 1] = g * 0.5
                image[..., 2] = b * 0.5
                image[..., 3] = 0.5
                self.texture_data = image.flatten()
                dpg.set_value(self.texture_id, self.texture_data)
            except Exception as e2:
                print(f"Ultimate fallback failed: {e2}")
                # Black screen as last resort
                self.texture_data = np.zeros(self.height * self.width * 4, dtype=np.float32)
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
