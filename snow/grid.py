"""Grid management for the snow simulation."""
import numpy as np
import random
from . import config

class Grid:
    def __init__(self):
        """Initialize the grid with current terminal dimensions."""
        dims = config.get_dimensions()
        self.width = dims['width']
        self.height = dims['height']
        self.visible_width = dims['visible_width']
        self.visible_start = dims['visible_start']
        self.floor_width = dims['floor_width']
        self.floor_start = dims['floor_start']
        
        # Initialize grid arrays
        self.grid = np.zeros((self.height, self.width), dtype=int)
        self.snowflake_chars = np.zeros((self.height, self.width), dtype=int)
        self.snowflake_speeds = np.ones((self.height, self.width), dtype=float)
        self.snowflake_colors = np.zeros((self.height, self.width), dtype=int)
        self.stationary_time = np.zeros((self.height, self.width), dtype=int)
        self.flake_existence_time = np.zeros((self.height, self.width), dtype=int)
        # Background layer
        self.background = np.zeros((self.height, self.width), dtype=int)
        self.background_colors = np.zeros((self.height, self.width), dtype=int)
        self.background_z = np.full((self.height, self.width), 255, dtype=int)  # Initialize all to back
        
        # Initialize background images from config
        self.init_background_images()

    def update_dimensions(self):
        """Update grid dimensions based on terminal size."""
        dims = config.get_dimensions()
        new_width = dims['width']
        new_height = dims['height']
        
        if new_width != self.width or new_height != self.height:
            new_grid = np.zeros((new_height, new_width), dtype=int)
            new_chars = np.zeros((new_height, new_width), dtype=int)
            new_speeds = np.ones((new_height, new_width), dtype=float)
            new_colors = np.zeros((new_height, new_width), dtype=int)
            new_stationary = np.zeros((new_height, new_width), dtype=int)
            new_existence = np.zeros((new_height, new_width), dtype=int)
            new_background = np.zeros((new_height, new_width), dtype=int)
            new_bg_colors = np.zeros((new_height, new_width), dtype=int)
            new_bg_z = np.full((new_height, new_width), 255, dtype=int)
            
            # Copy existing snow within new bounds
            copy_height = min(self.height, new_height)
            copy_width = min(self.width, new_width)
            new_grid[:copy_height, :copy_width] = self.grid[:copy_height, :copy_width]
            new_chars[:copy_height, :copy_width] = self.snowflake_chars[:copy_height, :copy_width]
            new_speeds[:copy_height, :copy_width] = self.snowflake_speeds[:copy_height, :copy_width]
            new_colors[:copy_height, :copy_width] = self.snowflake_colors[:copy_height, :copy_width]
            new_background[:copy_height, :copy_width] = self.background[:copy_height, :copy_width]
            new_bg_colors[:copy_height, :copy_width] = self.background_colors[:copy_height, :copy_width]
            new_bg_z[:copy_height, :copy_width] = self.background_z[:copy_height, :copy_width]
            
            # Update dimensions and arrays
            self.width = new_width
            self.height = new_height
            self.visible_width = dims['visible_width']
            self.visible_start = dims['visible_start']
            self.floor_width = dims['floor_width']
            self.floor_start = dims['floor_start']
            self.grid = new_grid
            self.snowflake_chars = new_chars
            self.snowflake_speeds = new_speeds
            self.snowflake_colors = new_colors
            self.stationary_time = new_stationary
            self.flake_existence_time = new_existence
            self.background = new_background
            self.background_colors = new_bg_colors
            self.background_z = new_bg_z

    def spawn_snowflakes(self, snowing, current_spawn_rate):
        """Spawn new snowflakes at the top of the screen."""
        if not snowing or np.sum(self.grid == config.SNOW_FLAKES) >= config.MAX_SNOWFLAKES_LIMIT:
            return
            
        # Try to spawn across more positions, but only in the visible area
        spawn_positions = random.sample(
            range(self.visible_start, self.visible_start + self.visible_width), 
            max(3, self.visible_width // 5)
        )
        
        for x in spawn_positions:
            if self.grid[0, x] == config.EMPTY:  # Always try to spawn if empty
                if random.random() < current_spawn_rate:
                    self.grid[0, x] = config.SNOW_FLAKES
                    self.snowflake_chars[0, x] = random.randint(0, len(config.SNOW_CHARS)-1)
                    self.snowflake_speeds[0, x] = random.uniform(0.3, 0.7)  # Keep speeds consistently light
                    # Generate color using active color scheme
                    self.snowflake_colors[0, x] = config.generate_snowflake_color()
                    self.flake_existence_time[0, x] = 0  # Reset existence time for new flake

    def clear_offscreen_bottom(self):
        """Clear bottom rows outside visible area if grid is nearly full."""
        if np.sum(self.grid == config.SNOW_FLAKES) >= config.MAX_SNOWFLAKES_LIMIT * 0.95:  # 95% full
            # Clear bottom row only outside visible area
            for x in range(self.width):
                if x < self.visible_start or x >= self.visible_start + self.visible_width:
                    self.grid[-1, x] = config.EMPTY
                    self.snowflake_chars[-1, x] = 0
                    self.snowflake_speeds[-1, x] = 1.0
                    self.snowflake_colors[-1, x] = 0

    def is_at_floor(self, y, x):
        """Check if the given position is at the floor."""
        return (y == self.height-2 and 
                x >= self.floor_start and 
                x < self.floor_start + self.floor_width)

    def get_cell(self, y, x):
        """Get the type of particle at the given position."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.grid[y, x]
        return None

    def set_cell(self, y, x, value):
        """Set a cell to a specific value and reset its properties."""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.grid[y, x] = value
            if value == config.EMPTY:
                self.snowflake_chars[y, x] = 0
                self.snowflake_speeds[y, x] = 1.0
                self.snowflake_colors[y, x] = 0
                self.stationary_time[y, x] = 0
                self.flake_existence_time[y, x] = 0

    def move_cell(self, from_y, from_x, to_y, to_x):
        """Move a cell from one position to another."""
        if (0 <= from_y < self.height and 0 <= from_x < self.width and
            0 <= to_y < self.height and 0 <= to_x < self.width):
            self.grid[to_y, to_x] = self.grid[from_y, from_x]
            self.snowflake_chars[to_y, to_x] = self.snowflake_chars[from_y, from_x]
            self.snowflake_speeds[to_y, to_x] = self.snowflake_speeds[from_y, from_x]
            self.snowflake_colors[to_y, to_x] = self.snowflake_colors[from_y, from_x]
            self.flake_existence_time[to_y, to_x] = self.flake_existence_time[from_y, from_x]
            self.set_cell(from_y, from_x, config.EMPTY)

    def increment_stationary_time(self, y, x):
        """Increment the stationary time for a cell."""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.stationary_time[y, x] += 1

    def reset_stationary_time(self, y, x):
        """Reset the stationary time for a cell."""
        if 0 <= y < self.height and 0 <= x < self.width:
            self.stationary_time[y, x] = 0

    def get_stationary_time(self, y, x):
        """Get the stationary time for a cell."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.stationary_time[y, x]
        return 0

    def get_snowflake_char(self, y, x):
        """Get the snowflake character index for a cell."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.snowflake_chars[y, x]
        return 0

    def get_display_char(self, y, x):
        """Get the actual character to display for a cell."""
        if 0 <= y < self.height and 0 <= x < self.width:
            cell_type = self.grid[y, x]
            # Snow particles are at z=127 (middle layer)
            if cell_type != config.EMPTY and self.background_z[y, x] > 127:
                if cell_type == config.SNOW_FLAKES:
                    char_idx = self.snowflake_chars[y, x]
                    if 0 <= char_idx < len(config.SNOW_CHARS):
                        return config.SNOW_CHARS[char_idx], self.snowflake_colors[y, x]
                elif cell_type == config.SNOW:
                    return config.SNOW_CHAR, None
                elif cell_type == config.PACKED_SNOW:
                    return config.PACKED_SNOW_CHAR, None
                elif cell_type == config.ICE:
                    return config.ICE_CHAR, None
            # Background is visible if no snow or if background is in front of snow layer
            if self.background[y, x] != 0 and (cell_type == config.EMPTY or self.background_z[y, x] <= 127):
                return chr(self.background[y, x]), self.background_colors[y, x]
        return ' ', None

    def set_background(self, y, x, char, color=None, z_order=255):
        """Set a background character and optionally its color and z-order at the given position."""
        if 0 <= y < self.height and 0 <= x < self.width:
            # Only update if new z-order is in front of existing
            if z_order <= self.background_z[y, x]:
                self.background[y, x] = ord(char)
                if color is not None:
                    self.background_colors[y, x] = color
                self.background_z[y, x] = z_order

    def init_background_images(self):
        """Initialize background images from configuration."""
        if not config.BACKGROUND_IMAGES or not config.SPRITES:
            return
            
        for image in config.BACKGROUND_IMAGES:
            # Get sprite definition
            sprite_name = image.get('sprite')
            if not sprite_name or sprite_name not in config.SPRITES:
                continue
                
            sprite = config.SPRITES[sprite_name]
            
            # Calculate position based on percentages of visible area
            x_pos = int((image['x'] / 100.0) * self.visible_width)
            y_pos = int((image['y'] / 100.0) * (self.height - 3))  # Account for status line
            
            # Adjust x position to be relative to visible area
            x_pos += self.visible_start
            
            # Get color configuration
            color_method = image.get('color_method', None)
            
            # Calculate image dimensions for relative positioning
            max_width = max(len(line) for line in sprite['lines'])
            max_height = len(sprite['lines'])
            
            # Get scale percentages (default to 100%)
            scale_x = image.get('scale_x', 100) / 100.0
            scale_y = image.get('scale_y', 100) / 100.0
            
            # Scale dimensions using nearest neighbor
            scaled_width = int(max_width * scale_x)
            scaled_height = int(max_height * scale_y)
            
            # Draw each line of the image with scaling
            for scaled_y in range(scaled_height):
                # Map scaled y back to original y using nearest neighbor
                y_offset = int(scaled_y / scale_y)
                if y_offset >= len(sprite['lines']):
                    continue
                    
                line = sprite['lines'][y_offset]
                for scaled_x in range(scaled_width):
                    # Map scaled x back to original x using nearest neighbor
                    x_offset = int(scaled_x / scale_x)
                    if x_offset >= len(line):
                        continue
                        
                    char = line[x_offset]
                    if char != ' ':  # Skip spaces to allow for transparency
                        # Calculate relative position (0-1) within the image
                        rel_x = x_offset / max_width if max_width > 1 else 0
                        rel_y = y_offset / max_height if max_height > 1 else 0
                        
                        # Generate color based on position
                        bg_color = (config._generate_background_color(color_method, rel_x, rel_y) 
                                  if color_method else None)
                        
                        self.set_background(
                            y_pos + scaled_y,
                            x_pos + scaled_x,
                            char,
                            bg_color,
                            image.get('z', 255)  # Get z-order from image config, default to back
                        )
