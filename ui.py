"""
UI Module for Neon & Anti-Neon Demo
Implements the Dark-Mode UI with Dear PyGui
"""

import dearpygui.dearpygui as dpg
import numpy as np
import math


class UI:
    """
    Handles the user interface using Dear PyGui
    """
    
    def __init__(self, width=1200, height=800):
        """Initialize the UI"""
        self.width = width
        self.height = height
        
        # Callback handlers
        self.on_hue_change = None
        self.on_saturation_change = None
        self.on_brightness_change = None
        self.on_fluorescence_change = None
        self.on_mode_toggle = None
        self.on_demo_toggled = None
        
        # UI State
        self.hue = 0.0
        self.saturation = 1.0
        self.brightness = 1.0
        self.fluorescence = 0.5
        self.neon_mode = True
        self.demo_running = False
        
        # Initialize Dear PyGui
        dpg.create_context()
        
        # Create texture for OpenGL rendering
        with dpg.texture_registry():
            # Initialize with a visible checkerboard pattern
            init_texture = np.ones((600, 800, 4), dtype=np.float32)
            for y in range(600):
                for x in range(800):
                    if (x // 50 + y // 50) % 2 == 0:
                        init_texture[y, x] = [0.2, 0.2, 0.2, 1.0]
                    else:
                        init_texture[y, x] = [0.3, 0.3, 0.3, 1.0]
            
            # Add a visible pattern to confirm texture loading
            center_x, center_y = 400, 300
            radius = 200
            for y in range(600):
                for x in range(800):
                    dx = x - center_x
                    dy = y - center_y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < radius:
                        # Create a rainbow gradient
                        angle = math.atan2(dy, dx)
                        if angle < 0:
                            angle += 2 * math.pi
                        hue = angle / (2 * math.pi)
                        r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
                        init_texture[y, x] = [r, g, b, 1.0]
            
            self.texture_id = dpg.add_dynamic_texture(800, 600, init_texture)
        
        # Set up global handler registry for tracking mouse events
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(callback=self._on_global_click)
            dpg.add_mouse_drag_handler(callback=self._on_global_drag)
            dpg.add_mouse_release_handler(callback=self._on_global_release)
        
        dpg.configure_app(docking=True, docking_space=True)
        dpg.create_viewport(title="Neon & Anti-Neon Demo", width=width, height=height, clear_color=[0.1, 0.1, 0.12, 1.0])
        dpg.setup_dearpygui()
        
        # Create UI elements
        self._create_ui()
    
    def _create_ui(self):
        """Create all UI elements"""
        # Primary window
        with dpg.window(label="Neon & Anti-Neon Demo", no_close=True, no_collapse=True, no_move=True, no_resize=True, tag="primary_window"):
            dpg.set_primary_window(dpg.last_item(), True)
            
            # Two panel layout
            with dpg.group(horizontal=True):
                # Left panel - OpenGL Rendering
                with dpg.child_window(width=800, height=600, border=False, tag="render_panel"):
                    dpg.add_image(self.texture_id, width=800, height=600, tag="display_image")
                
                # Right panel - Controls
                with dpg.child_window(width=380, height=600, border=False, tag="control_panel"):
                    dpg.add_text("Color Settings", color=[0.9, 0.9, 0.9])
                    dpg.add_separator()
                    
                    # Mode toggle
                    with dpg.group(horizontal=True):
                        with dpg.group():
                            dpg.add_text("Mode:")
                        with dpg.group():
                            dpg.add_radio_button(
                                items=["Neon", "Anti-Neon"], 
                                default_value="Neon",
                                callback=self._on_mode_change,
                                horizontal=True,
                                tag="mode_selector"
                            )
                    
                    dpg.add_spacer(height=10)
                    
                    # Hue wheel
                    dpg.add_text("Hue Selection")
                    
                    # Create the hue wheel
                    self._draw_hue_wheel()
                    
                    # No need to add hue selector here as it's created in _draw_hue_wheel
                    
                    dpg.add_spacer(height=10)
                    
                    # Sliders with explicit tags for debugging
                    dpg.add_text("Saturation")
                    self.saturation_slider = dpg.add_slider_float(
                        default_value=1.0,
                        min_value=0.0,
                        max_value=1.0,
                        width=350,
                        callback=self._on_saturation_slider,
                        tag="saturation_slider"
                    )
                    
                    dpg.add_text("Brightness")
                    self.brightness_slider = dpg.add_slider_float(
                        default_value=1.0,
                        min_value=0.0,
                        max_value=1.0,
                        width=350,
                        callback=self._on_brightness_slider,
                        tag="brightness_slider"
                    )
                    
                    dpg.add_text("Fluorescence")
                    self.fluorescence_slider = dpg.add_slider_float(
                        default_value=0.5,
                        min_value=0.0,
                        max_value=1.0,
                        width=350,
                        callback=self._on_fluorescence_slider,
                        tag="fluorescence_slider"
                    )
                    
                    dpg.add_spacer(height=20)
                    
                    # Demo mode
                    dpg.add_text("Demo Mode", color=[0.9, 0.9, 0.9])
                    dpg.add_separator()
                    
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Start Demo",
                            width=115,
                            callback=lambda: self._on_demo_button(True),
                            tag="start_demo_button"
                        )
                        dpg.add_button(
                            label="Stop Demo",
                            width=115,
                            callback=lambda: self._on_demo_button(False),
                            tag="stop_demo_button"
                        )
                        dpg.add_button(
                            label="Reset",
                            width=115,
                            callback=self._on_reset_button,
                            tag="reset_button"
                        )
        
        # Debug information window
        with dpg.window(label="Debug Info", width=300, height=250, pos=[10, 650], tag="debug_window"):
            dpg.add_text("FPS: --", tag="fps_text")
            dpg.add_text("Current Mode: Neon", tag="mode_text")
            dpg.add_text("Hue: 0.0", tag="hue_text")
            dpg.add_text("Saturation: 1.0", tag="saturation_text")
            dpg.add_text("Brightness: 1.0", tag="brightness_text")
            dpg.add_text("Fluorescence: 0.5", tag="fluorescence_text")
            dpg.add_text("Last Event: None", tag="event_text")
            dpg.add_text("Mouse Position: --", tag="mouse_pos_text")
            dpg.add_button(label="Test Controls", callback=self._test_controls, tag="test_button")
    
    def _test_controls(self):
        """Test if controls are responding"""
        print("Testing controls...")
        
        # Change hue
        self.hue = 120.0  # Green
        self._update_hue_selector()
        if self.on_hue_change:
            self.on_hue_change(self.hue)
            
        # Update debug display
        if dpg.does_item_exist("hue_text"):
            dpg.set_value("hue_text", f"Hue: {self.hue:.1f}")
            
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", "Last Event: Test Controls")
    
    def _draw_hue_wheel(self):
        """Draw the hue color wheel"""
        # Clear previous items
        if dpg.does_item_exist("hue_wheel_drawlist"):
            dpg.delete_item("hue_wheel_drawlist")
            
        # Create a new drawlist
        self.hue_wheel_drawlist = dpg.add_drawlist(width=350, height=350, tag="hue_wheel_drawlist")
        
        # Draw the base circle with a more visible background
        dpg.draw_circle(
            center=[175, 175],
            radius=150,
            color=[0.3, 0.3, 0.3],
            fill=[0.2, 0.2, 0.2],
            parent=self.hue_wheel_drawlist
        )
        
        # Draw colored segments around the wheel using triangles
        segments = 36
        center_x, center_y = 175, 175
        radius = 150
        inner_radius = 50  # Add an inner circle to make the wheel more visible
        
        # Draw the inner circle (white for visibility)
        dpg.draw_circle(
            center=[center_x, center_y],
            radius=inner_radius,
            color=[0.8, 0.8, 0.8],
            fill=[0.7, 0.7, 0.7],
            parent=self.hue_wheel_drawlist
        )
        
        for i in range(segments):
            hue = i * 360 / segments
            r, g, b = self._hsv_to_rgb(hue / 360, 1.0, 1.0)
            
            # Calculate points for the segment
            angle1 = i * 2 * math.pi / segments
            angle2 = (i + 1) * 2 * math.pi / segments
            
            # Outer points
            x1 = center_x + radius * math.cos(angle1)
            y1 = center_y + radius * math.sin(angle1)
            x2 = center_x + radius * math.cos(angle2)
            y2 = center_y + radius * math.sin(angle2)
            
            # Inner points
            x3 = center_x + inner_radius * math.cos(angle1)
            y3 = center_y + inner_radius * math.sin(angle1)
            x4 = center_x + inner_radius * math.cos(angle2)
            y4 = center_y + inner_radius * math.sin(angle2)
            
            # Draw a quad for each segment (using two triangles)
            dpg.draw_triangle(
                p1=[x1, y1],
                p2=[x2, y2],
                p3=[x3, y3],
                color=[r, g, b],
                fill=[r, g, b],
                parent=self.hue_wheel_drawlist
            )
            
            dpg.draw_triangle(
                p1=[x2, y2],
                p2=[x3, y3],
                p3=[x4, y4],
                color=[r, g, b],
                fill=[r, g, b],
                parent=self.hue_wheel_drawlist
            )
        
        # No need to create a selector here, it will be created in _update_hue_selector
        
        # Update the selector position based on current hue
        self._update_hue_selector()
    
    def _on_global_click(self, sender, app_data):
        """Handle mouse click anywhere"""
        # Get mouse position from dpg
        mouse_pos = dpg.get_mouse_pos(local=False)
        print(f"Mouse click detected at {mouse_pos}")
        
        # Check for hue wheel interaction
        self._check_hue_wheel_click(mouse_pos)
        
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", f"Last Event: Mouse Click ({mouse_pos[0]:.0f}, {mouse_pos[1]:.0f})")
    
    def _on_global_drag(self, sender, app_data):
        """Handle mouse drag anywhere"""
        # Get absolute mouse position instead of relative
        mouse_pos = dpg.get_mouse_pos(local=False)
        
        # Update mouse position in debug window
        if dpg.does_item_exist("mouse_pos_text"):
            dpg.set_value("mouse_pos_text", f"Mouse Position: {mouse_pos[0]:.0f}, {mouse_pos[1]:.0f}")
        
        # Handle dragging on the hue wheel
        self._check_hue_wheel_click(mouse_pos)
    
    def _on_global_release(self, sender, app_data):
        """Handle mouse release anywhere"""
        print(f"Mouse release at {app_data}")
    
    def _check_hue_wheel_click(self, mouse_pos):
        """Check if click is within the hue wheel and handle it"""
        # Only proceed if hue wheel exists
        if not dpg.does_item_exist("hue_wheel_drawlist"):
            return
        
        # Get the position and size of the hue wheel drawlist
        wheel_pos = dpg.get_item_rect_min("hue_wheel_drawlist")
        wheel_size = dpg.get_item_rect_size("hue_wheel_drawlist")
        
        # Calculate center and radius
        center_x = wheel_pos[0] + wheel_size[0] / 2
        center_y = wheel_pos[1] + wheel_size[1] / 2
        radius = min(wheel_size[0], wheel_size[1]) / 2 * 0.9  # Use 90% of radius for better interaction
        
        # Debug output
        print(f"Wheel position: {wheel_pos}, size: {wheel_size}, center: ({center_x}, {center_y}), radius: {radius}")
        print(f"Mouse position: {mouse_pos}, distance from center: {math.sqrt((mouse_pos[0] - center_x)**2 + (mouse_pos[1] - center_y)**2)}")
        
        # Check if mouse is within the wheel circle
        dx = mouse_pos[0] - center_x
        dy = mouse_pos[1] - center_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance <= radius:
            # Calculate angle (hue)
            angle = math.atan2(dy, dx)
            if angle < 0:
                angle += 2 * math.pi
            
            # Convert to degrees (0-360)
            self.hue = (angle * 180 / math.pi) % 360
            
            # Update debug display
            if dpg.does_item_exist("hue_text"):
                dpg.set_value("hue_text", f"Hue: {self.hue:.1f}")
            
            if dpg.does_item_exist("event_text"):
                dpg.set_value("event_text", f"Last Event: Hue Wheel ({self.hue:.1f}°)")
            
            # Update selector position
            self._update_hue_selector()
            
            # Call callback
            if self.on_hue_change:
                self.on_hue_change(self.hue)
                
            print(f"Hue changed to: {self.hue:.1f}°")
    
    def _update_hue_selector(self):
        """Update the position of the hue selector based on current hue"""
        # Delete old selector if it exists
        if dpg.does_item_exist("hue_selector"):
            dpg.delete_item("hue_selector")
            
        # Get the position and size of the hue wheel drawlist
        wheel_pos = dpg.get_item_rect_min("hue_wheel_drawlist")
        wheel_size = dpg.get_item_rect_size("hue_wheel_drawlist")
        
        # Calculate center and radius
        center_x = wheel_pos[0] + wheel_size[0] / 2
        center_y = wheel_pos[1] + wheel_size[1] / 2
        radius = min(wheel_size[0], wheel_size[1]) / 2 * 0.8  # Use 80% of radius for selector
        
        # Convert hue to radians
        angle_rad = self.hue * math.pi / 180
        
        # Calculate position on the circle
        selector_x = center_x + radius * math.cos(angle_rad)
        selector_y = center_y + radius * math.sin(angle_rad)
        
        # Create a new selector at the calculated position
        dpg.draw_circle(
            center=[selector_x, selector_y],
            radius=8,
            color=[1, 1, 1],
            fill=[1, 1, 1],
            parent="hue_wheel_drawlist",
            tag="hue_selector"
        )
    
    def _on_saturation_slider(self, sender, app_data):
        """Handle saturation slider change"""
        print(f"Saturation changed: {app_data}")
        self.saturation = app_data
        
        # Update debug display
        if dpg.does_item_exist("saturation_text"):
            dpg.set_value("saturation_text", f"Saturation: {self.saturation:.2f}")
        
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", f"Last Event: Saturation ({self.saturation:.2f})")
            
        if self.on_saturation_change:
            self.on_saturation_change(self.saturation)
    
    def _on_brightness_slider(self, sender, app_data):
        """Handle brightness slider change"""
        print(f"Brightness changed: {app_data}")
        self.brightness = app_data
        
        # Update debug display
        if dpg.does_item_exist("brightness_text"):
            dpg.set_value("brightness_text", f"Brightness: {self.brightness:.2f}")
        
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", f"Last Event: Brightness ({self.brightness:.2f})")
            
        if self.on_brightness_change:
            self.on_brightness_change(self.brightness)
    
    def _on_fluorescence_slider(self, sender, app_data):
        """Handle fluorescence slider change"""
        print(f"Fluorescence changed: {app_data}")
        self.fluorescence = app_data
        
        # Update debug display
        if dpg.does_item_exist("fluorescence_text"):
            dpg.set_value("fluorescence_text", f"Fluorescence: {self.fluorescence:.2f}")
        
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", f"Last Event: Fluorescence ({self.fluorescence:.2f})")
            
        if self.on_fluorescence_change:
            self.on_fluorescence_change(self.fluorescence)
    
    def _on_mode_change(self, sender, app_data):
        """Handle mode toggle change"""
        print(f"Mode changed: {app_data}")
        self.neon_mode = (app_data == "Neon")
        
        # Update debug display
        if dpg.does_item_exist("mode_text"):
            dpg.set_value("mode_text", f"Current Mode: {'Neon' if self.neon_mode else 'Anti-Neon'}")
        
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", f"Last Event: Mode Change ({app_data})")
            
        if self.on_mode_toggle:
            self.on_mode_toggle(self.neon_mode)
    
    def _on_demo_button(self, start):
        """Handle demo button press"""
        print(f"Demo button: {'Start' if start else 'Stop'}")
        self.demo_running = start
        
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", f"Last Event: Demo {'Start' if start else 'Stop'}")
            
        if self.on_demo_toggled:
            self.on_demo_toggled(start)
    
    def _on_reset_button(self):
        """Handle reset button press"""
        print("Reset button pressed")
        # Reset to default values
        self.hue = 0.0
        self.saturation = 1.0
        self.brightness = 1.0
        self.fluorescence = 0.5
        self.neon_mode = True
        self.demo_running = False
        
        # Update UI controls
        dpg.set_value("saturation_slider", 1.0)
        dpg.set_value("brightness_slider", 1.0)
        dpg.set_value("fluorescence_slider", 0.5)
        dpg.set_value("mode_selector", "Neon")
        
        # Update UI to reflect changes
        self._update_hue_selector()
        
        # Update debug displays
        if dpg.does_item_exist("hue_text"):
            dpg.set_value("hue_text", f"Hue: {self.hue:.1f}")
        if dpg.does_item_exist("saturation_text"):
            dpg.set_value("saturation_text", f"Saturation: {self.saturation:.2f}")
        if dpg.does_item_exist("brightness_text"):
            dpg.set_value("brightness_text", f"Brightness: {self.brightness:.2f}")
        if dpg.does_item_exist("fluorescence_text"):
            dpg.set_value("fluorescence_text", f"Fluorescence: {self.fluorescence:.2f}")
        if dpg.does_item_exist("mode_text"):
            dpg.set_value("mode_text", f"Current Mode: {'Neon' if self.neon_mode else 'Anti-Neon'}")
        if dpg.does_item_exist("event_text"):
            dpg.set_value("event_text", "Last Event: Reset")
        
        # Call callbacks
        if self.on_hue_change:
            self.on_hue_change(self.hue)
        if self.on_saturation_change:
            self.on_saturation_change(self.saturation)
        if self.on_brightness_change:
            self.on_brightness_change(self.brightness)
        if self.on_fluorescence_change:
            self.on_fluorescence_change(self.fluorescence)
        if self.on_mode_toggle:
            self.on_mode_toggle(self.neon_mode)
        if self.on_demo_toggled:
            self.on_demo_toggled(False)
    
    def update_texture(self, pixel_data):
        """Update the texture with new pixel data (RGBA float32 array)"""
        # Make sure the texture exists before updating
        if dpg.does_item_exist(self.texture_id):
            # Skip type checking and reshaping for performance in normal operation
            # Only perform these checks if the shape doesn't match exactly
            if pixel_data.shape != (600, 800, 4):
                # Try to reshape if possible, otherwise use default
                try:
                    pixel_data = pixel_data.reshape(600, 800, 4)
                except ValueError:
                    print("Error: Could not reshape texture data")
                    return
            
            # Ensure data is float32 for best performance with DPG
            if pixel_data.dtype != np.float32:
                pixel_data = pixel_data.astype(np.float32)
            
            # Update the texture with the pixel data
            dpg.set_value(self.texture_id, pixel_data)
            
        # Update FPS display - only calculate when needed
        if dpg.does_item_exist("fps_text") and dpg.get_frame_count() % 10 == 0:
            current_fps = 1.0 / dpg.get_delta_time() if dpg.get_delta_time() > 0 else 0
            dpg.set_value("fps_text", f"FPS: {current_fps:.1f}")
    
    def start(self):
        """Start the UI main loop"""
        dpg.show_viewport()
        print("Viewport shown")
        
    def should_exit(self):
        """Check if the UI should exit"""
        return dpg.is_dearpygui_running() is False
        
    def cleanup(self):
        """Clean up the UI resources"""
        dpg.destroy_context()
    
    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB (all values in 0-1 range)"""
        if s == 0.0:
            return v, v, v
            
        i = int(h * 6)
        f = (h * 6) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        i %= 6
        
        if i == 0:
            return v, t, p
        elif i == 1:
            return q, v, p
        elif i == 2:
            return p, v, t
        elif i == 3:
            return p, q, v
        elif i == 4:
            return t, p, v
        else:
            return v, p, q
