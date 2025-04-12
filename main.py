"""
Neon & Anti-Neon Demo
Main application that integrates all components
"""

import numpy as np
import dearpygui.dearpygui as dpg
import time

from color_engine import ColorEngine

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
        dpg.setup_dearpygui()
        
        # Create texture for rendering
        self.width = 800
        self.height = 600
        
        # Create texture registry
        with dpg.texture_registry():
            # Initialize with black - use zeros_like for better performance
            self.texture_data = np.zeros((self.height, self.width, 4), dtype=np.float32)
            self.texture_id = dpg.add_dynamic_texture(self.width, self.height, self.texture_data)
        
        # Pre-calculate coordinates for faster rendering
        y_coords, x_coords = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
        center_x, center_y = self.width // 2, self.height // 2
        self.dx = x_coords - center_x
        self.dy = y_coords - center_y
        
        # Pre-calculate distances once - this is used in every frame
        self.distances = np.sqrt(self.dx**2 + self.dy**2) / (self.width // 2)
        
        # Pre-calculate normalized coordinates for shader-like effects
        self.norm_x = self.dx / (self.width // 2)
        self.norm_y = self.dy / (self.height // 2)
        
        # Pre-calculate common masks
        self.circle_mask = self.distances < 0.95
        self.border_mask = (self.distances >= 0.95) & (self.distances <= 1.0)
        
        # For FPS calculation - initialize before rendering
        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0
        self.frame_times = np.zeros(10)  # Store last 10 frame times for smoother FPS
        self.frame_time_idx = 0
        
        # For adaptive rendering
        self.target_frame_time = 1.0 / 60.0  # Target 60 FPS
        self.skip_frames = 0
        self.ray_quality = 1  # 0=no rays, 1=some rays, 2=all rays
        self.last_quality_check = time.time()
        
        # Create UI
        self._create_ui()
        
        # Create initial pattern
        self._render_frame()
        
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
                    
                    # Reset Button
                    dpg.add_button(label="Reset", callback=self._on_reset)
                    
                    dpg.add_spacer(height=20)
                    
                    # Debug info
                    with dpg.collapsing_header(label="Debug Info", default_open=True):
                        dpg.add_text("FPS: 0", tag="fps_text")
                        dpg.add_text("Current Mode: Neon", tag="mode_text")
                        dpg.add_text("Hue: 0.0", tag="hue_text")
                        dpg.add_text("Saturation: 1.0", tag="saturation_text")
                        dpg.add_text("Brightness: 1.0", tag="brightness_text")
                        dpg.add_text("Fluorescence: 0.5", tag="fluorescence_text")
    
    def _on_hue_change(self, sender, app_data):
        """Handle hue change"""
        self.color_engine.set_hue(app_data)
        dpg.set_value("hue_text", f"Hue: {app_data:.1f}")
    
    def _on_saturation_change(self, sender, app_data):
        """Handle saturation change"""
        self.color_engine.set_saturation(app_data)
        dpg.set_value("saturation_text", f"Saturation: {app_data:.2f}")
    
    def _on_brightness_change(self, sender, app_data):
        """Handle brightness change"""
        self.color_engine.set_brightness(app_data)
        dpg.set_value("brightness_text", f"Brightness: {app_data:.2f}")
    
    def _on_fluorescence_change(self, sender, app_data):
        """Handle fluorescence change"""
        self.color_engine.set_fluorescence(app_data)
        dpg.set_value("fluorescence_text", f"Fluorescence: {app_data:.2f}")
    
    def _on_mode_change(self, sender, app_data):
        """Handle mode toggle"""
        self.color_engine.set_neon_mode(app_data == "Neon")
        dpg.set_value("mode_text", f"Current Mode: {app_data}")
    
    def _on_reset(self):
        """Handle reset button"""
        # Reset color engine to defaults
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
        """Render a frame"""
        try:
            # Get current color settings
            h, s, v = self.color_engine.get_hsv()
            r, g, b = self.color_engine.get_rgb()
            
            # Create circular mask once and reuse
            circle_mask = self.circle_mask
            
            # Clear texture data to background color
            self.texture_data[...] = [0.05, 0.05, 0.05, 1.0]
            
            if self.color_engine.neon_mode:
                # Neon mode - bright, saturated
                # Calculate bloom intensity based on fluorescence
                bloom = self.color_engine.get_bloom_intensity()
                
                # Pre-calculate intensity for better performance
                # Use numpy's vectorized operations for better performance
                intensity = np.clip(1.0 - self.distances * (1.2 - 0.5 * bloom), 0, 1.0) ** 2
                
                # Apply base color with intensity
                self.texture_data[..., 0] = np.where(circle_mask, r * intensity, 0.05)
                self.texture_data[..., 1] = np.where(circle_mask, g * intensity, 0.05)
                self.texture_data[..., 2] = np.where(circle_mask, b * intensity, 0.05)
                
                # Add center glow - vectorized operation
                center_glow = np.clip(1.0 - self.distances * 2.5, 0, 1.0) ** 2 * bloom * 1.2
                self.texture_data[..., 0] = np.maximum(self.texture_data[..., 0], center_glow * r)
                self.texture_data[..., 1] = np.maximum(self.texture_data[..., 1], center_glow * g)
                self.texture_data[..., 2] = np.maximum(self.texture_data[..., 2], center_glow * b)
                
                # Add rays - only if bloom is significant and ray quality allows
                if bloom > 0.2 and self.ray_quality > 0:
                    # Pre-calculate ray parameters
                    ray_intensity = 0.3 * bloom
                    ray_width = 0.05
                    
                    # Determine how many rays to render based on quality
                    num_rays = 4 if self.ray_quality == 1 else 8
                    
                    # Calculate rays on-the-fly (more reliable than pre-calculated masks)
                    for i in range(num_rays):
                        angle = i * (2 * np.pi / num_rays)
                        ray_x = np.cos(angle)
                        ray_y = np.sin(angle)
                        
                        # Calculate dot product for each pixel with ray direction
                        dot_product = (self.norm_x * ray_x) + (self.norm_y * ray_y)
                        
                        # Create ray mask
                        ray_mask = (np.abs(dot_product) < ray_width) & circle_mask
                        
                        # Apply ray effect
                        if np.any(ray_mask):
                            self.texture_data[ray_mask, 0] = np.minimum(self.texture_data[ray_mask, 0] + ray_intensity * r, 1.0)
                            self.texture_data[ray_mask, 1] = np.minimum(self.texture_data[ray_mask, 1] + ray_intensity * g, 1.0)
                            self.texture_data[ray_mask, 2] = np.minimum(self.texture_data[ray_mask, 2] + ray_intensity * b, 1.0)
            else:
                # Anti-neon mode - darker, desaturated
                # Get RGB directly from color_engine which already applies low S/V for anti-neon
                r, g, b = self.color_engine.get_rgb() # Use the already adjusted RGB
                
                intensity = np.clip(1.0 - self.distances * 1.2, 0, 1.0)
                
                # Apply colors with intensity
                self.texture_data[..., 0] = np.where(circle_mask, r * intensity, 0.05)
                self.texture_data[..., 1] = np.where(circle_mask, g * intensity, 0.05)
                self.texture_data[..., 2] = np.where(circle_mask, b * intensity, 0.05)
                
                # Add dark rim effect - vectorized
                dark_rim = np.clip(1.0 - np.abs(self.distances - 0.7) * 10, 0, 1.0) * 0.7
                self.texture_data[..., 0] = np.maximum(0, self.texture_data[..., 0] - dark_rim * 0.2)
                self.texture_data[..., 1] = np.maximum(0, self.texture_data[..., 1] - dark_rim * 0.2)
                self.texture_data[..., 2] = np.maximum(0, self.texture_data[..., 2] - dark_rim * 0.2)
            
            # Add border - vectorized
            border_mask = self.border_mask
            border_intensity = 0.3 if self.color_engine.neon_mode else 0.15
            self.texture_data[border_mask, 0] = border_intensity
            self.texture_data[border_mask, 1] = border_intensity
            self.texture_data[border_mask, 2] = border_intensity
            
            # Set alpha to full opacity
            self.texture_data[..., 3] = 1.0
            
            # Update texture
            dpg.set_value(self.texture_id, self.texture_data)
        except Exception as e:
            print(f"Error in render frame: {e}")
    
    def run(self):
        """Run the application"""
        print("Use the sliders to adjust colors & parameters.")
        print("Toggle between Neon & Anti-Neon modes.")
        print("Press ESC or close the window to exit.")
        
        # Show viewport
        dpg.show_viewport()
        
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
        print("Neon & Anti-Neon Demo closed.")


if __name__ == "__main__":
    app = NeonApp()
    app.run()
