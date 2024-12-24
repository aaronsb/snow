"""Main entry point for snow simulation."""
import random
import signal
import time
from threading import Thread

from . import config
from .grid import Grid
from .physics import Physics
from .renderer import Renderer

class SnowSimulation:
    def __init__(self):
        """Initialize the snow simulation."""
        self.grid = Grid()
        self.physics = Physics(self.grid)
        self.renderer = Renderer(self.grid)
        self.running = True
        self.state = config.DEFAULT_STATE.copy()
        # Track last mouse position for movement
        self.last_mouse_x = None
        self.last_mouse_y = None
        # Track status visibility
        self.show_status = False

    def handle_exit(self, signum, frame):
        """Handle exit gracefully."""
        self.running = False
        time.sleep(0.1)
        print(self.renderer.term.normal)
        exit(0)

    def physics_loop(self):
        """Continuous physics updates."""
        while self.running:
            if self.state['snowing']:
                self.grid.spawn_snowflakes(self.state['snowing'], 
                                         self.state['current_spawn_rate'])
            
            self.physics.update_wind()
            
            # Update backoff factor based on snow height
            self.physics.current_backoff = self.physics.calculate_backoff_factor()
            
            # Clear offscreen particles if needed
            self.grid.clear_offscreen_bottom()
            
            # Update existence time for all snow flakes
            for y in range(self.grid.height-2, -1, -1):
                for x in range(self.grid.width):
                    cell = self.grid.get_cell(y, x)
                    if cell == config.EMPTY:
                        continue
                        
                    # Check for blocked cells
                    below_blocked = (y == self.grid.height-2 or 
                                   self.grid.get_cell(y+1, x) != config.EMPTY)
                    at_floor = self.grid.is_at_floor(y, x)
                    
                    if below_blocked or at_floor:
                        self.grid.increment_stationary_time(y, x)
                    
                    # Handle state transitions
                    if (self.physics.handle_compression(y, x) or
                        self.physics.handle_snow_packing(y, x) or
                        self.physics.handle_ice_formation(y, x) or
                        self.physics.handle_melting(y, x, self.state['temperature'])):
                        continue
                    
                    # Calculate and apply movement
                    moves = self.physics.calculate_movement(y, x)
                    if not self.physics.apply_movement(y, x, moves):
                        # If no movement, might need to reset stationary time
                        if not (below_blocked or at_floor):
                            self.grid.reset_stationary_time(y, x)
            
            time.sleep(config.GRAVITY_DELAY)

    def handle_input(self, key):
        """Handle keyboard input."""
        if key == 'q':
            self.running = False
            return True
        elif key == ' ':  # Space to toggle snow
            self.state['snowing'] = not self.state['snowing']
        elif key.name == 'KEY_UP':  # Up arrow to increase spawn rate
            self.state['current_spawn_rate'] = min(
                self.state['current_spawn_rate'] + config.SPAWN_RATE_STEP, 
                config.MAX_SPAWN_RATE
            )
        elif key.name == 'KEY_DOWN':  # Down arrow to decrease spawn rate
            self.state['current_spawn_rate'] = max(
                self.state['current_spawn_rate'] - config.SPAWN_RATE_STEP, 
                config.MIN_SPAWN_RATE
            )
        elif key.name == 'KEY_LEFT':  # Left arrow for wind
            self.physics.set_target_wind(
                -config.MAX_WIND_STRENGTH * random.uniform(0.7, 1.0)
            )
        elif key.name == 'KEY_RIGHT':  # Right arrow for wind
            self.physics.set_target_wind(
                config.MAX_WIND_STRENGTH * random.uniform(0.7, 1.0)
            )
        elif key in ['+', '=']:  # Increase temperature
            self.state['temperature'] = min(self.state['temperature'] + 1, 10)
        elif key in ['-', '_']:  # Decrease temperature
            self.state['temperature'] = max(self.state['temperature'] - 1, -10)
        elif key.lower() == 'h':  # Toggle help display (upper or lowercase)
            self.show_status = not self.show_status
        
        return False

    def run(self):
        """Run the snow simulation."""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.handle_exit)
        
        # Start physics thread
        physics_thread = Thread(target=self.physics_loop)
        physics_thread.daemon = True
        physics_thread.start()
        
        # Enable mouse reporting
        print('\033[?1000h')  # Enable mouse click tracking
        print('\033[?1002h')  # Enable mouse movement tracking
        print('\033[?1015h')  # Enable urxvt style extended mouse reporting
        print('\033[?1006h')  # Enable SGR extended mouse reporting
        
        with self.renderer.term.fullscreen(), \
             self.renderer.term.cbreak(), \
             self.renderer.term.hidden_cursor():
            
            self.renderer.clear_screen()
            
            while self.running:
                val = self.renderer.term.inkey(timeout=0.01)
                
                # Handle mouse events
                if val == '\x1b':  # ESC sequence start
                    seq = val
                    while True:
                        next_char = self.renderer.term.inkey(timeout=0.01)
                        if not next_char:
                            break
                        seq += next_char
                        if seq.endswith('M') or seq.endswith('m'):
                            break
                    
                    # Parse SGR mouse sequence: \x1b[<Cb;Cx;Cy[M|m]
                    if seq.startswith('\x1b[<') and (seq.endswith('M') or seq.endswith('m')):
                        try:
                            parts = seq[3:-1].split(';')
                            btn = int(parts[0])
                            x = int(parts[1]) - 1  # Convert to 0-based
                            y = int(parts[2]) - 1  # Convert to 0-based
                            
                            # Process mouse events
                            is_press = seq.endswith('M')
                            is_release = seq.endswith('m')
                            
                            # Adjust coordinates for grid position
                            y = y - 2  # Account for status lines at top
                            x = x + self.grid.visible_start
                            
                            if 0 <= y < self.grid.height and self.grid.visible_start <= x < self.grid.visible_start + self.grid.visible_width:
                                if btn == 0:  # Left click
                                    if is_press:
                                        # Start tracking mouse position
                                        self.last_mouse_x = x
                                        self.last_mouse_y = y
                                    elif is_release:
                                        # Clear last position on release
                                        self.last_mouse_x = None
                                        self.last_mouse_y = None
                                        # On mouse up, create or destroy snow
                                        cell = self.grid.get_cell(y, x)
                                        if cell in [config.SNOW, config.PACKED_SNOW, config.ICE]:
                                            # Remove snow/ice in a 7x7 grid
                                            for dy in range(-3, 4):
                                                for dx in range(-3, 4):
                                                    ny, nx = y + dy, x + dx
                                                    if (0 <= ny < self.grid.height and 
                                                        self.grid.visible_start <= nx < self.grid.visible_start + self.grid.visible_width):
                                                        cell = self.grid.get_cell(ny, nx)
                                                        if cell in [config.SNOW, config.PACKED_SNOW, config.ICE]:
                                                            self.grid.set_cell(ny, nx, config.EMPTY)
                                        elif cell in [config.EMPTY, config.SNOW_FLAKES]:
                                            # Add snow in a 7x7 grid
                                            for dy in range(-3, 4):
                                                for dx in range(-3, 4):
                                                    ny, nx = y + dy, x + dx
                                                    if (0 <= ny < self.grid.height and 
                                                        self.grid.visible_start <= nx < self.grid.visible_start + self.grid.visible_width):
                                                        if self.grid.get_cell(ny, nx) == config.EMPTY:
                                                            self.grid.set_cell(ny, nx, config.SNOW)
                                elif btn == 32 and self.last_mouse_x is not None:  # Mouse move while held (btn 32 is motion)
                                    # Calculate movement direction
                                    move_dx = x - self.last_mouse_x
                                    move_dy = y - self.last_mouse_y
                                        
                                    # Only process if there was movement
                                    if move_dx != 0 or move_dy != 0:
                                        # Normalize movement direction
                                        magnitude = (move_dx * move_dx + move_dy * move_dy) ** 0.5
                                        if magnitude > 0:
                                            norm_dx = move_dx / magnitude
                                            norm_dy = move_dy / magnitude
                                            
                                            # Push particles in 7x7 grid in movement direction
                                            for dy in range(-3, 4):
                                                for dx in range(-3, 4):
                                                    ny, nx = y + dy, x + dx
                                                    if (0 <= ny < self.grid.height and 
                                                        self.grid.visible_start <= nx < self.grid.visible_start + self.grid.visible_width):
                                                        cell = self.grid.get_cell(ny, nx)
                                                        if cell in [config.SNOW, config.PACKED_SNOW, config.ICE, config.SNOW_FLAKES]:
                                                            # Push in movement direction
                                                            target_x = int(nx + norm_dx)
                                                            target_y = int(ny + norm_dy)
                                                            
                                                            # Check if target position is valid and empty
                                                            if (0 <= target_y < self.grid.height and
                                                                self.grid.visible_start <= target_x < self.grid.visible_start + self.grid.visible_width and
                                                                self.grid.get_cell(target_y, target_x) == config.EMPTY):
                                                                self.grid.move_cell(ny, nx, target_y, target_x)
                                    
                                    # Update last position
                                    self.last_mouse_x = x
                                    self.last_mouse_y = y
                        except (IndexError, ValueError):
                            pass  # Invalid mouse sequence
                elif self.handle_input(val):
                    break
                
                self.renderer.render_grid(self.state, self.show_status)
        
        # Disable mouse reporting and restore terminal
        print('\033[?1000l')  # Disable mouse click tracking
        print('\033[?1002l')  # Disable mouse movement tracking
        print('\033[?1015l')  # Disable urxvt style extended mouse reporting
        print('\033[?1006l')  # Disable SGR extended mouse reporting
        print(self.renderer.term.normal)

def main():
    """Entry point for the snow simulation."""
    simulation = SnowSimulation()
    simulation.run()

if __name__ == '__main__':
    main()
