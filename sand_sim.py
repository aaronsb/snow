#!/usr/bin/env python3
import blessed
import numpy as np
import time
import sys
from threading import Thread
import signal

term = blessed.Terminal()

# Constants
SAND = 1
EMPTY = 0
SAND_CHAR = '█'
CURSOR = '+'
GRAVITY_DELAY = 0.05  # seconds between gravity updates

# Initialize dimensions and grid
WIDTH = term.width
HEIGHT = term.height - 3  # Account for instructions and bottom padding
grid = np.zeros((HEIGHT, WIDTH), dtype=int)
cursor_x = WIDTH // 2
cursor_y = HEIGHT // 2

def update_dimensions():
    """Update grid dimensions based on terminal size."""
    global WIDTH, HEIGHT, grid, cursor_x, cursor_y
    new_width = term.width
    new_height = term.height - 3  # Account for instructions and bottom padding
    
    if new_width != WIDTH or new_height != HEIGHT:
        # Create new grid with updated dimensions
        new_grid = np.zeros((new_height, new_width), dtype=int)
        
        if new_width < WIDTH or new_height < HEIGHT:
            # Handle shrinking dimensions by pushing sand inward/upward
            
            # First handle width reduction (push sand leftward)
            if new_width < WIDTH:
                for y in range(HEIGHT):
                    sand_count = 0
                    # Count sand particles that would be cut off
                    for x in range(new_width, WIDTH):
                        if grid[y, x] == SAND:
                            sand_count += 1
                    
                    # Push sand leftward starting from rightmost valid position
                    if sand_count > 0:
                        x = new_width - 1
                        while sand_count > 0 and x >= 0:
                            if grid[y, x] == EMPTY:
                                grid[y, x] = SAND
                                sand_count -= 1
                            x -= 1
            
            # Then handle height reduction (push sand upward)
            if new_height < HEIGHT:
                for x in range(min(WIDTH, new_width)):
                    sand_count = 0
                    # Count sand particles that would be cut off
                    for y in range(new_height, HEIGHT):
                        if grid[y, x] == SAND:
                            sand_count += 1
                    
                    # Push sand upward starting from bottom valid position
                    if sand_count > 0:
                        y = new_height - 1
                        while sand_count > 0 and y >= 0:
                            if grid[y, x] == EMPTY:
                                grid[y, x] = SAND
                                sand_count -= 1
                            y -= 1
        
        # Copy the adjusted grid to the new grid
        copy_height = min(HEIGHT, new_height)
        copy_width = min(WIDTH, new_width)
        new_grid[:copy_height, :copy_width] = grid[:copy_height, :copy_width]
        
        # Update globals
        WIDTH = new_width
        HEIGHT = new_height
        grid = new_grid
        
        # Keep cursor within bounds
        cursor_x = min(cursor_x, WIDTH - 1)
        cursor_y = min(cursor_y, HEIGHT - 1)

def clear_screen():
    """Clear the terminal screen."""
    print(term.home + term.clear)

def render_grid():
    """Render the current state of the grid."""
    update_dimensions()  # Check for terminal resize
    output = []
    # Add instructions at the top
    output.append(term.white + "Arrow keys: Move cursor | Space: Place sand | Q: Quit\n\n")
    
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x == cursor_x and y == cursor_y:
                output.append(term.white + CURSOR)
            elif grid[y, x] == SAND:
                output.append(term.yellow + SAND_CHAR)
            else:
                output.append(' ')
        output.append('\n')
    sys.stdout.write(term.home + ''.join(output))
    sys.stdout.flush()

def apply_gravity():
    """Apply gravity to sand particles."""
    # We iterate from bottom to top, right to left
    for y in range(HEIGHT-2, -1, -1):
        for x in range(WIDTH-1, -1, -1):
            if grid[y, x] == SAND:
                # Check directly below
                if grid[y+1, x] == EMPTY:
                    grid[y+1, x] = SAND
                    grid[y, x] = EMPTY
                # Check below and to the right
                elif x < WIDTH-1 and grid[y+1, x+1] == EMPTY:
                    grid[y+1, x+1] = SAND
                    grid[y, x] = EMPTY
                # Check below and to the left
                elif x > 0 and grid[y+1, x-1] == EMPTY:
                    grid[y+1, x-1] = SAND
                    grid[y, x] = EMPTY

def physics_loop():
    """Continuous physics updates."""
    global running
    while running:
        apply_gravity()
        time.sleep(GRAVITY_DELAY)

def handle_exit(signum, frame):
    """Handle exit gracefully."""
    global running
    running = False
    time.sleep(0.1)
    print(term.normal)
    sys.exit(0)

def main():
    global running, cursor_x, cursor_y, WIDTH, HEIGHT, grid
    running = True
    
    # Set up signal handler
    signal.signal(signal.SIGINT, handle_exit)
    
    # Start physics thread
    physics_thread = Thread(target=physics_loop)
    physics_thread.daemon = True
    physics_thread.start()
    
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        # Ensure initial dimensions are correct
        update_dimensions()
        # Initial render
        clear_screen()
        render_grid()
        
        # Main game loop
        while running:
            # Get input (non-blocking)
            key = term.inkey(timeout=0.01)
            
            if key == 'q':
                running = False
                break
            elif key.name == 'KEY_UP' and cursor_y > 0:
                cursor_y -= 1
            elif key.name == 'KEY_DOWN' and cursor_y < HEIGHT - 1:
                cursor_y += 1
            elif key.name == 'KEY_LEFT' and cursor_x > 0:
                cursor_x -= 1
            elif key.name == 'KEY_RIGHT' and cursor_x < WIDTH - 1:
                cursor_x += 1
            elif key == ' ':  # Space key to place sand
                grid[cursor_y, cursor_x] = SAND
            
            render_grid()
            
    print(term.normal)

if __name__ == '__main__':
    main()
