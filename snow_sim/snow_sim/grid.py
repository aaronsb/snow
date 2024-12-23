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
        self.stationary_time = np.zeros((self.height, self.width), dtype=int)
        self.flake_existence_time = np.zeros((self.height, self.width), dtype=int)

    def update_dimensions(self):
        """Update grid dimensions based on terminal size."""
        dims = config.get_dimensions()
        new_width = dims['width']
        new_height = dims['height']
        
        if new_width != self.width or new_height != self.height:
            new_grid = np.zeros((new_height, new_width), dtype=int)
            new_chars = np.zeros((new_height, new_width), dtype=int)
            new_speeds = np.ones((new_height, new_width), dtype=float)
            new_stationary = np.zeros((new_height, new_width), dtype=int)
            new_existence = np.zeros((new_height, new_width), dtype=int)
            
            # Copy existing snow within new bounds
            copy_height = min(self.height, new_height)
            copy_width = min(self.width, new_width)
            new_grid[:copy_height, :copy_width] = self.grid[:copy_height, :copy_width]
            new_chars[:copy_height, :copy_width] = self.snowflake_chars[:copy_height, :copy_width]
            new_speeds[:copy_height, :copy_width] = self.snowflake_speeds[:copy_height, :copy_width]
            
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
            self.stationary_time = new_stationary
            self.flake_existence_time = new_existence

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
                self.stationary_time[y, x] = 0
                self.flake_existence_time[y, x] = 0

    def move_cell(self, from_y, from_x, to_y, to_x):
        """Move a cell from one position to another."""
        if (0 <= from_y < self.height and 0 <= from_x < self.width and
            0 <= to_y < self.height and 0 <= to_x < self.width):
            self.grid[to_y, to_x] = self.grid[from_y, from_x]
            self.snowflake_chars[to_y, to_x] = self.snowflake_chars[from_y, from_x]
            self.snowflake_speeds[to_y, to_x] = self.snowflake_speeds[from_y, from_x]
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
        """Get the snowflake character for a cell."""
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.snowflake_chars[y, x]
        return 0
