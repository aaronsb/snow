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
        
        return False

    def run(self):
        """Run the snow simulation."""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.handle_exit)
        
        # Start physics thread
        physics_thread = Thread(target=self.physics_loop)
        physics_thread.daemon = True
        physics_thread.start()
        
        with self.renderer.term.fullscreen(), \
             self.renderer.term.cbreak(), \
             self.renderer.term.hidden_cursor():
            
            self.renderer.clear_screen()
            
            while self.running:
                key = self.renderer.term.inkey(timeout=0.01)
                if self.handle_input(key):
                    break
                self.renderer.render_grid(self.state)
        
        print(self.renderer.term.normal)

def main():
    """Entry point for the snow simulation."""
    simulation = SnowSimulation()
    simulation.run()

if __name__ == '__main__':
    main()
