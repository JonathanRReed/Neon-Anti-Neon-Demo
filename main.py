"""
Neon & Anti-Neon Demo
Main application that integrates all components
"""

import numpy as np
import dearpygui.dearpygui as dpg
import time
import moderngl as mgl
import os
from datetime import datetime

from color_engine import ColorEngine


class ShaderRenderer:
    """
    GPU-accelerated renderer using ModernGL and GLSL shaders
    """
    
    def __init__(self, width=800, height=600):
        """Initialize the shader renderer (context will be created lazily)"""
        self.width = width
        self.height = height
        self.ctx = None
        self.neon_program = None
        self.antineon_program = None
        self.vbo = None
        self.vao = None
        self.framebuffer = None
    
    def _ensure_context(self):
        """Create ModernGL context and GPU resources if not already created.
        This must be called after DearPyGui has shown the viewport so an OpenGL
        context is current.
        """
        if self.ctx is not None:
            return
        # Attach to the current OpenGL context provided by DearPyGui
        self.ctx = mgl.create_context(require=330)
        # Load shaders and GPU buffers
        self._load_shaders()
        self._create_quad()
        self.framebuffer = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((self.width, self.height), 4, dtype='f4')]
        )
        
    def _load_shaders(self):
        """Load GLSL shaders from files"""
        try:
            with open('shaders/vertex.glsl', 'r') as f:
                vertex_shader = f.read()
            with open('shaders/neon_fragment.glsl', 'r') as f:
                self.neon_fragment = f.read()
            with open('shaders/antineon_fragment.glsl', 'r') as f:
                self.antineon_fragment = f.read()
                
            # Create shader programs
            self.neon_program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=self.neon_fragment
            )
            self.antineon_program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=self.antineon_fragment
            )
            
        except FileNotFoundError as e:
            print(f"Shader file not found: {e}")
            raise
        except Exception as e:
            print(f"Error loading shaders: {e}")
            raise
    
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
        """Render a frame using shaders"""
        # Ensure GL context and resources are ready
        self._ensure_context()
        
        # Bind framebuffer
        self.framebuffer.use()
        self.ctx.clear(0.05, 0.05, 0.05, 1.0)  # Dark background
        
        # Choose shader program based on mode
        if color_engine.neon_mode:
            program = self.neon_program
            # Set neon shader uniforms (dual-color core/halo) below
        else:
            program = self.antineon_program
            program['shadow_intensity'] = 0.5  # Adjust as needed
        
        # Set uniforms from ColorEngine
        if color_engine.neon_mode:
            cr, cg, cb = color_engine.get_rgb()
            hr, hg, hb = color_engine.get_halo_rgb()
            program['core_color'] = (cr, cg, cb)
            program['halo_color'] = (hr, hg, hb)
            program['halo_width'] = float(color_engine.halo_width)
            program['halo_intensity'] = float(color_engine.halo_intensity)
            program['bloom_intensity'] = float(color_engine.get_bloom_intensity())
        else:
            r, g, b = color_engine.get_rgb()
            program['color'] = (r, g, b)
        
        # Bind vertex array with current program
        vao = self.ctx.vertex_array(program, [(self.vbo, '2f 2f', 'in_position', 'in_texcoord')])
        
        # Render quad
        vao.render(mgl.TRIANGLE_STRIP)
        
        # Read pixels from framebuffer
        pixels = self.framebuffer.read(components=4, dtype='f4')
        
        # Convert to numpy array and reshape
        texture_data = np.frombuffer(pixels, dtype=np.float32).reshape(self.height, self.width, 4)
        
        return texture_data
    
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
        """Initialize the application"""
        print("Initializing Neon & Anti-Neon Demo...")
        
        # Create color engine
        self.color_engine = ColorEngine()
        
        # Initialize DearPyGui
        dpg.create_context()
        dpg.create_viewport(title="Neon & Anti-Neon Demo", width=1200, height=800)
        
        # Set modern dark theme
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
                dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 235, 255))
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (130, 130, 150, 200))
                dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (90, 90, 140, 120))
                
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
        dpg.setup_dearpygui()
        
        # Prepare shader renderer (lazy init after viewport is shown)
        self.renderer = ShaderRenderer(width=800, height=600)
        
        # Create texture for rendering
        self.width = 800
        self.height = 600
        
        # Create texture registry
        with dpg.texture_registry():
            # Initialize with black - use zeros_like for better performance
            self.texture_data = np.zeros((self.height, self.width, 4), dtype=np.float32)
            self.texture_id = dpg.add_dynamic_texture(self.width, self.height, self.texture_data)
        
        # For FPS calculation - initialize before rendering
        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0
        self.frame_times = np.zeros(10)  # Store last 10 frame times for smoother FPS
        self.frame_time_idx = 0
        
        # For adaptive rendering
        self.target_frame_time = 1.0 / 60.0  # Target 60 FPS
        self.skip_frames = 0
        self.ray_quality = 0
        self.last_quality_check = time.time()
        
        # Rendering mode flags
        self.use_gpu = True
        self._gpu_failed_once = False
        
        # Create UI
        self._create_ui()
        
        # Do not render yet; ModernGL will attach to DPG context after viewport is shown
        print("Initialization complete!")
    
    def _create_ui(self):
        """Create the user interface"""
        # Main window
        with dpg.window(label="Neon & Anti-Neon Demo", no_close=True, tag="main_window"):
            dpg.set_primary_window("main_window", True)
            
            # Two-panel layout
            with dpg.group(horizontal=True):
                # Left panel - Rendering
                with dpg.child_window(width=800, height=600, tag="render_panel"):
                    dpg.add_image(self.texture_id, width=800, height=600)
                
                # Right panel - Controls
                with dpg.child_window(width=380, height=600, tag="control_panel"):
                    dpg.add_text("Color Settings", color=[0.9, 0.9, 0.9])
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
                        width=350,
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
                        width=350,
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
                        width=350,
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
                        width=350,
                        tag="fluorescence_slider"
                    )
                    
                    dpg.add_spacer(height=20)
                    
                    # Preset buttons
                    dpg.add_text("Quick Presets", color=[0.9, 0.9, 0.9])
                    dpg.add_separator()
                    
                    # Halo controls (for neon look and neon-brown)
                    dpg.add_text("Halo Width")
                    dpg.add_slider_float(
                        default_value=self.color_engine.halo_width,
                        min_value=0.02,
                        max_value=0.4,
                        width=350,
                        callback=self._on_halo_width_change,
                        tag="halo_width_slider"
                    )
                    dpg.add_text("Halo Intensity")
                    dpg.add_slider_float(
                        default_value=self.color_engine.halo_intensity,
                        min_value=0.0,
                        max_value=2.0,
                        width=350,
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
                                        width=105,
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
                        width=350,
                        callback=self._on_export_image,
                        tag="export_button"
                    )
                    
                    dpg.add_spacer(height=20)
            
            # Bottom info panel across the width
            with dpg.child_window(width=1180, height=160, tag="info_panel"):
                with dpg.group(horizontal=True):
                    with dpg.group():
                        dpg.add_text("System & Renderer", color=[0.9, 0.9, 0.9])
                        dpg.add_separator()
                        dpg.add_text("FPS: 0", tag="fps_text")
                        dpg.add_text("Renderer: GPU", tag="renderer_text")
                        dpg.add_text("Current Mode: Neon", tag="mode_text")
                    with dpg.group():
                        dpg.add_text("Color State", color=[0.9, 0.9, 0.9])
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
    
    def _on_saturation_change(self, sender, app_data):
        """Handle saturation change"""
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_saturation=app_data, duration=0.3)
        else:
            self.color_engine.set_saturation(app_data)
        dpg.set_value("saturation_text", f"Saturation: {app_data:.2f}")
    
    def _on_brightness_change(self, sender, app_data):
        """Handle brightness change"""
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_brightness=app_data, duration=0.3)
        else:
            self.color_engine.set_brightness(app_data)
        dpg.set_value("brightness_text", f"Brightness: {app_data:.2f}")
    
    def _on_fluorescence_change(self, sender, app_data):
        """Handle fluorescence change"""
        if hasattr(self.color_engine, 'animate_to'):
            self.color_engine.animate_to(target_fluorescence=app_data, duration=0.3)
        else:
            self.color_engine.set_fluorescence(app_data)
        dpg.set_value("fluorescence_text", f"Fluorescence: {app_data:.2f}")
    
    def _on_halo_width_change(self, sender, app_data):
        """Handle halo width change"""
        if hasattr(self.color_engine, 'set_halo_width'):
            self.color_engine.set_halo_width(app_data)
    
    def _on_halo_intensity_change(self, sender, app_data):
        """Handle halo intensity change"""
        if hasattr(self.color_engine, 'set_halo_intensity'):
            self.color_engine.set_halo_intensity(app_data)
    
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
    
    def _on_preset_select(self, preset_name):
        """Handle preset button click"""
        if hasattr(self.color_engine, 'apply_preset'):
            success = self.color_engine.apply_preset(preset_name, duration=1.2)
            if success:
                print(f"Applied preset: {preset_name}")
            else:
                print(f"Failed to apply preset: {preset_name}")
    
    def _on_export_image(self):
        """Export current rendering as PNG image"""
        try:
            # Create exports directory if it doesn't exist
            export_dir = "exports"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"neon_demo_{timestamp}.png"
            filepath = os.path.join(export_dir, filename)
            
            # Get current texture data and convert to image format
            # The texture data is already in RGBA float32 format (0-1 range)
            # Convert to uint8 (0-255 range) for image saving
            image_data = (self.texture_data * 255).astype(np.uint8)
            
            # Flip vertically (OpenGL to image coordinate system)
            image_data = np.flipud(image_data)
            
            # Save using PIL or similar - for now, save raw data
            # Note: In a real implementation, you'd use PIL/Pillow to save as PNG
            print(f"Image export would save to: {filepath}")
            print(f"Image size: {image_data.shape}")
            
            # For now, just save as numpy array (placeholder)
            np.save(filepath.replace('.png', '.npy'), image_data)
            
            print(f"Exported image: {filename}")
            
        except Exception as e:
            print(f"Export failed: {e}")
    
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
                duration=0.8
            )
        else:
            # Fallback to instant reset
            self.color_engine.set_hue(0.0)
            self.color_engine.set_saturation(1.0)
            self.color_engine.set_brightness(1.0)
            self.color_engine.set_fluorescence(0.5)
            self.color_engine.set_neon_mode(True)
        
        # Reset UI controls
        dpg.set_value("hue_text", "Hue: 0.0")
        dpg.set_value("saturation_text", "Saturation: 1.0")
        dpg.set_value("brightness_text", "Brightness: 1.0")
        dpg.set_value("fluorescence_text", "Fluorescence: 0.5")
        dpg.set_value("mode_text", "Current Mode: Neon")
    
    def _calculate_fps(self):
        """Calculate frames per second"""
        current_time = time.time()
        elapsed = current_time - self.last_time
        
        # Store frame time in circular buffer for averaging
        self.frame_times[self.frame_time_idx] = elapsed
        self.frame_time_idx = (self.frame_time_idx + 1) % len(self.frame_times)
        
        # Calculate FPS based on average of recent frame times
        # Skip zeros in the buffer (not filled yet)
        valid_times = self.frame_times[self.frame_times > 0]
        if len(valid_times) > 0:
            avg_frame_time = np.mean(valid_times)
            self.fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        # Update FPS counter every 10 frames for smoother display
        self.frame_count += 1
        if self.frame_count >= 10:
            # Update FPS display
            if dpg.does_item_exist("fps_text"):
                dpg.set_value("fps_text", f"FPS: {self.fps:.1f}")
                
                # Adjust rendering quality based on performance
                if self.fps < 30 and self.skip_frames < 2:
                    # If FPS is too low, increase frame skipping
                    self.skip_frames += 1
                    
                    # Also reduce ray quality if in neon mode
                    if self.color_engine.neon_mode and self.ray_quality > 0:
                        self.ray_quality -= 1
                        
                elif self.fps > 50 and self.skip_frames > 0:
                    # If FPS is high enough, reduce frame skipping
                    self.skip_frames -= 1
                    
                    # Gradually increase ray quality if possible
                    if current_time - self.last_quality_check > 2.0:  # Check every 2 seconds
                        if self.ray_quality < 2:
                            self.ray_quality += 1
                        self.last_quality_check = current_time
            
            self.frame_count = 0
            
        # Update last time for next calculation
        self.last_time = current_time
    
    def _render_frame(self):
        """Render a frame using GPU shaders if available, else CPU fallback"""
        # Update animations and demo mode
        if hasattr(self.color_engine, 'update_animation'):
            self.color_engine.update_animation()
        if hasattr(self.color_engine, 'update_demo'):
            self.color_engine.update_demo()
        
        if self.use_gpu:
            try:
                # Use shader renderer for GPU-accelerated rendering
                self.texture_data = self.renderer.render_frame(self.color_engine)
                # Update texture
                dpg.set_value(self.texture_id, self.texture_data)
                return
            except Exception as e:
                # Disable GPU path after first failure to avoid log spam
                if not self._gpu_failed_once:
                    print(f"GPU render unavailable, switching to CPU fallback: {e}")
                    self._gpu_failed_once = True
                self.use_gpu = False
                if dpg.does_item_exist("renderer_text"):
                    dpg.set_value("renderer_text", "Renderer: CPU")
                if dpg.does_item_exist("renderer_mode"):
                    dpg.set_value("renderer_mode", "CPU")
        
        # CPU fallback rendering
        self._fallback_render()
    
    def _fallback_render(self):
        """Simple CPU-based fallback rendering"""
        try:
            r, g, b = self.color_engine.get_rgb()
            
            # Create simple colored circle
            center_x, center_y = self.width // 2, self.height // 2
            y_coords, x_coords = np.ogrid[:self.height, :self.width]
            distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)
            
            # Create circular gradient
            max_dist = min(center_x, center_y)
            intensity = np.clip(1.0 - distances / max_dist, 0, 1.0)
            
            self.texture_data[..., 0] = r * intensity
            self.texture_data[..., 1] = g * intensity  
            self.texture_data[..., 2] = b * intensity
            self.texture_data[..., 3] = intensity
            
            dpg.set_value(self.texture_id, self.texture_data)
        except Exception as e:
            print(f"Fallback render failed: {e}")
    
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
            if delta_time < 0.005:  # If we're running faster than 200 FPS
                time.sleep(0.001)  # Sleep for 1ms to reduce CPU usage
        
        # Clean up
        dpg.destroy_context()
        if hasattr(self, 'renderer'):
            self.renderer.cleanup()
        print("Neon & Anti-Neon Demo closed.")


if __name__ == "__main__":
    app = NeonApp()
    app.run()
