#!/usr/bin/env python3
import blessed
import numpy as np
import time
import sys
from threading import Thread
import signal
import random

term = blessed.Terminal()

# Constants
SNOW_FLAKES = 1
SNOW = 2
PACKED_SNOW = 3
ICE = 4
EMPTY = 0
MELT_CHANCE = 0.001  # Base chance for melting

# Wind settings
MAX_WIND_STRENGTH = 0.8  # Maximum wind force
WIND_RAMP_SPEED = 0.05  # How quickly wind builds up/dies down

# State
snowing = True  # Start with snow enabled
current_spawn_rate = 0.1  # Start with 10% spawn chance
wind_strength = 0  # Current wind strength (-1 to 1, negative = left, positive = right)
target_wind_strength = 0  # Wind strength we're ramping towards
temperature = 0  # Temperature affects melt chance (-10 to 10)
BASE_MELT_CHANCE = 0.001  # Base chance for melting
SNOW_CHARS = ['❄', '❅', '❆', '*', '+', '.', '⠋', '⠛', '⠟', '⠿', '⡿', '⣿']  # Different snowflake characters
SNOW_CHAR = '░'  # ASCII 176 for snow
PACKED_SNOW_CHAR = '▒'  # ASCII 177 for packed snow
ICE_CHAR = '▓'  # ASCII 178 for ice
GRAVITY_DELAY = 0.05  # Base falling speed - matches rules document
MAX_SNOWFLAKES_LIMIT = 2000  # Maximum limit for total snowflakes
MIN_SPAWN_RATE = 0.01  # Minimum spawn chance (1%)
MAX_SPAWN_RATE = 0.5   # Maximum spawn chance (50%)
SPAWN_RATE_STEP = 0.05  # How much to adjust spawn rate by


# Initialize dimensions and grid
VISIBLE_WIDTH = term.width
WIDTH = int(VISIBLE_WIDTH * 2.0)  # Extend simulation 50% on each side
HEIGHT = term.height - 3  # Account for instructions and bottom padding
VISIBLE_START = int(VISIBLE_WIDTH * 0.5)  # Where visible portion starts
FLOOR_WIDTH = int(VISIBLE_WIDTH * 1.5)  # Floor extends 25% on each side
FLOOR_START = int(VISIBLE_WIDTH * 0.25)  # Where floor starts
grid = np.zeros((HEIGHT, WIDTH), dtype=int)
snowflake_chars = np.zeros((HEIGHT, WIDTH), dtype=int)  # Track which char to use for each flake
snowflake_speeds = np.ones((HEIGHT, WIDTH), dtype=float)  # Individual falling speeds
stationary_time = np.zeros((HEIGHT, WIDTH), dtype=int)  # Track how long flakes have been still
flake_existence_time = np.zeros((HEIGHT, WIDTH), dtype=int)  # Track how long flakes have existed

def update_dimensions():
    """Update grid dimensions based on terminal size."""
    global WIDTH, VISIBLE_WIDTH, HEIGHT, grid, snowflake_chars, VISIBLE_START, FLOOR_WIDTH, FLOOR_START, flake_existence_time
    new_visible_width = term.width
    new_width = int(new_visible_width * 2.0)
    new_height = term.height - 3
    
    if new_width != WIDTH or new_height != HEIGHT:
        new_grid = np.zeros((new_height, new_width), dtype=int)
        new_chars = np.zeros((new_height, new_width), dtype=int)
        new_speeds = np.ones((new_height, new_width), dtype=float)
        new_stationary = np.zeros((new_height, new_width), dtype=int)
        new_existence = np.zeros((new_height, new_width), dtype=int)
        
        # Copy existing snow within new bounds
        copy_height = min(HEIGHT, new_height)
        copy_width = min(WIDTH, new_width)
        new_grid[:copy_height, :copy_width] = grid[:copy_height, :copy_width]
        new_chars[:copy_height, :copy_width] = snowflake_chars[:copy_height, :copy_width]
        new_speeds[:copy_height, :copy_width] = snowflake_speeds[:copy_height, :copy_width]
        
        VISIBLE_WIDTH = new_visible_width
        WIDTH = new_width
        HEIGHT = new_height
        VISIBLE_START = int(VISIBLE_WIDTH * 0.5)
        FLOOR_WIDTH = int(VISIBLE_WIDTH * 1.5)
        FLOOR_START = int(VISIBLE_WIDTH * 0.25)
        grid = new_grid
        snowflake_chars = new_chars
        snowflake_speeds = new_speeds
        stationary_time = new_stationary
        flake_existence_time = new_existence

def clear_screen():
    """Clear the terminal screen."""
    print(term.home + term.clear)

def render_grid():
    """Render the current state of the grid."""
    update_dimensions()
    output = []
    status = "ON" if snowing else "OFF"
    spawn_rate_percent = int(current_spawn_rate * 100)
    # Show wind direction with arrows
    wind_indicator = ""
    if wind_strength < 0:
        wind_indicator = f"← Wind: {abs(int(wind_strength * 100))}%"
    elif wind_strength > 0:
        wind_indicator = f"Wind: {abs(int(wind_strength * 100))}% →"
    else:
        wind_indicator = "No Wind"
        
    output.append(term.white + f"Q: Quit | SPACE: Toggle Snow [{status}] | ↑/↓: Adjust Spawn Rate ({spawn_rate_percent}%) | ←/→: Wind | +/-: Temp ({temperature}) | {wind_indicator}\n\n")
    
    # Only render the visible portion
    for y in range(HEIGHT):
        for x in range(VISIBLE_START, VISIBLE_START + VISIBLE_WIDTH):
            if grid[y, x] == SNOW_FLAKES:
                output.append(term.white + SNOW_CHARS[snowflake_chars[y, x]])
            elif grid[y, x] == SNOW:
                output.append(term.white + SNOW_CHAR)
            elif grid[y, x] == PACKED_SNOW:
                output.append(term.white + PACKED_SNOW_CHAR)
            elif grid[y, x] == ICE:
                output.append(term.white + ICE_CHAR)
            else:
                output.append(' ')
        output.append('\n')
    sys.stdout.write(term.home + ''.join(output))
    sys.stdout.flush()

def update_wind():
    """Update wind strength based on target."""
    global wind_strength
    if wind_strength < target_wind_strength:
        wind_strength = min(wind_strength + WIND_RAMP_SPEED, target_wind_strength)
    elif wind_strength > target_wind_strength:
        wind_strength = max(wind_strength - WIND_RAMP_SPEED, target_wind_strength)

def spawn_snowflakes():
    """Spawn new snowflakes at the top of the screen."""
    if not snowing or np.sum(grid == SNOW_FLAKES) >= MAX_SNOWFLAKES_LIMIT:
        return
        
    # Try to spawn across more positions, but only in the visible area
    spawn_positions = random.sample(range(VISIBLE_START, VISIBLE_START + VISIBLE_WIDTH), 
                                 max(3, VISIBLE_WIDTH // 5))
    for x in spawn_positions:
        if grid[0, x] == EMPTY:  # Always try to spawn if empty
            if random.random() < current_spawn_rate:
                grid[0, x] = SNOW_FLAKES
                snowflake_chars[0, x] = random.randint(0, len(SNOW_CHARS)-1)
                snowflake_speeds[0, x] = random.uniform(0.3, 0.7)  # Keep speeds consistently light
                flake_existence_time[0, x] = 0  # Reset existence time for new flake

def apply_gravity():
    """Apply gravity and wind effects to snowflakes."""
    global stationary_time, flake_existence_time
    # Only clear bottom rows outside visible area if we're really full
    if np.sum(grid == SNOW_FLAKES) >= MAX_SNOWFLAKES_LIMIT * 0.95:  # 95% full
        # Clear bottom row only outside visible area
        for x in range(WIDTH):
            if x < VISIBLE_START or x >= VISIBLE_START + VISIBLE_WIDTH:
                grid[-1, x] = EMPTY
                snowflake_chars[-1, x] = 0
                snowflake_speeds[-1, x] = 1.0
    
    # Update existence time for all snow flakes
    flake_existence_time[grid == SNOW_FLAKES] += 1
    
    # We iterate from bottom to top to prevent snowflakes from passing through each other
    for y in range(HEIGHT-2, -1, -1):
        for x in range(WIDTH):
                if grid[y, x] in [SNOW_FLAKES, SNOW, PACKED_SNOW]:
                    # Check for compression - delete flakes below snow blocks
                    if grid[y, x] == SNOW_FLAKES and y > 0 and grid[y-1, x] == SNOW:
                        grid[y, x] = EMPTY
                        snowflake_chars[y, x] = 0
                        snowflake_speeds[y, x] = 1.0
                        stationary_time[y, x] = 0
                        continue

                    # Check for any type of blocked cell below (snowflakes, snow, packed snow, ice)
                    below_blocked = (y == HEIGHT-2) or grid[y+1, x] != EMPTY
                    at_floor = (y == HEIGHT-2 and x >= FLOOR_START and x < FLOOR_START + FLOOR_WIDTH)
                    
                    if below_blocked or at_floor:
                        stationary_time[y, x] += 1
                    
                    # Convert snow flakes based on density
                    if grid[y, x] == SNOW_FLAKES:
                        # Count nearby and above snow flakes
                        flake_neighbors = []
                        # Check 3x3 area per rules document
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                ny, nx = y + dy, x + dx
                                if (0 <= ny < HEIGHT and 0 <= nx < WIDTH and 
                                    grid[ny, nx] == SNOW_FLAKES):
                                    flake_neighbors.append((ny, nx))
                        
                        # Convert if enough flakes and been still for longer
                        if len(flake_neighbors) >= 6 and stationary_time[y, x] > 20:  # Require 6+ neighbors per rules
                            # Remove the neighboring flakes that were "compressed"
                            for ny, nx in flake_neighbors:
                                grid[ny, nx] = EMPTY
                                snowflake_chars[ny, nx] = 0
                                snowflake_speeds[ny, nx] = 1.0
                                stationary_time[ny, nx] = 0
                            # Convert center flake to snow
                            grid[y, x] = SNOW
                            continue
                    
                    # Convert snow to packed snow based on neighbors
                    elif grid[y, x] == SNOW and stationary_time[y, x] > 1000:  # Match rules document timing
                        # Count nearby snow
                        snow_count = 0
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                ny, nx = y + dy, x + dx
                                if (0 <= ny < HEIGHT and 0 <= nx < WIDTH and 
                                    grid[ny, nx] in [SNOW, PACKED_SNOW]):
                                    snow_count += 1
                        
                        # Convert if enough snow nearby and snow/packed below
                        if snow_count >= 7 and y < HEIGHT-1 and grid[y+1, x] in [SNOW, PACKED_SNOW, ICE]:  # Match rules document requirement
                            grid[y, x] = PACKED_SNOW
                            continue
                    
                    # Convert packed snow to ice based on neighbors
                    elif grid[y, x] == PACKED_SNOW and stationary_time[y, x] > 2000:  # Match rules document timing
                        # Count nearby packed snow
                        packed_count = 0
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                ny, nx = y + dy, x + dx
                                if (0 <= ny < HEIGHT and 0 <= nx < WIDTH and 
                                    grid[ny, nx] in [PACKED_SNOW, ICE]):
                                    packed_count += 1
                        
                        # Convert if enough packed snow nearby and packed/ice below
                        if packed_count >= 8 and y < HEIGHT-1 and grid[y+1, x] in [PACKED_SNOW, ICE]:  # Match rules document requirement
                            grid[y, x] = ICE
                            continue
                    
                    # Apply melting/compression effects
                    # Calculate melt chance based on temperature
                    melt_chance = BASE_MELT_CHANCE * (2 ** (temperature / 2))  # Exponential scaling
                    if random.random() < melt_chance:
                        # Check if particle can melt/evaporate
                        can_melt = False
                        # Don't allow melting if we're at the bottom boundary
                        if y == HEIGHT-2 and x >= FLOOR_START and x < FLOOR_START + FLOOR_WIDTH:
                            can_melt = False
                        else:
                            for dy in range(-1, 2):
                                for dx in range(-1, 2):
                                    ny, nx = y + dy, x + dx
                                    # Don't count bottom boundary as empty space
                                    if (ny == HEIGHT-1 or 
                                        (ny == HEIGHT-2 and nx >= FLOOR_START and nx < FLOOR_START + FLOOR_WIDTH)):
                                        continue
                                    if (0 <= ny < HEIGHT and 0 <= nx < WIDTH and 
                                        (grid[ny, nx] == EMPTY or grid[ny, nx] == SNOW_FLAKES)):
                                        can_melt = True
                                        break
                                if can_melt:
                                    break

                        if grid[y, x] == SNOW_FLAKES:
                            # Flakes simply evaporate
                            grid[y, x] = EMPTY
                            snowflake_chars[y, x] = 0
                            snowflake_speeds[y, x] = 1.0
                            continue
                        elif can_melt:  # Only allow melting if adjacent to empty space or snowflake
                            if grid[y, x] == SNOW:
                                if random.random() < 0.2:  # 20% chance to compress
                                    grid[y, x] = PACKED_SNOW
                                else:  # 80% chance to evaporate
                                    grid[y, x] = EMPTY
                                stationary_time[y, x] = 0
                                continue
                            elif grid[y, x] == PACKED_SNOW:
                                if random.random() < 0.3:  # 30% chance to compress to ice
                                    grid[y, x] = ICE
                                elif random.random() < 0.1:  # 10% chance to evaporate
                                    grid[y, x] = EMPTY
                                stationary_time[y, x] = 0
                                continue
                            elif grid[y, x] == ICE:
                                if random.random() < 0.05:  # 5% chance to melt away
                                    grid[y, x] = EMPTY
                                stationary_time[y, x] = 0
                                continue
                else:
                    stationary_time[y, x] = 0

                # Different physics for each type
                if grid[y, x] == SNOW_FLAKES:
                    # Check for any snow-type blocks nearby before considering movement
                    has_snow_nearby = False
                    # Check below
                    if y < HEIGHT-1:
                        has_snow_nearby = grid[y+1, x] in [SNOW, PACKED_SNOW, ICE]
                        if x > 0:
                            has_snow_nearby = has_snow_nearby or grid[y+1, x-1] in [SNOW, PACKED_SNOW, ICE]
                        if x < WIDTH-1:
                            has_snow_nearby = has_snow_nearby or grid[y+1, x+1] in [SNOW, PACKED_SNOW, ICE]
                    # Check above to prevent passing through from below
                    if y > 0:
                        has_snow_nearby = has_snow_nearby or grid[y-1, x] in [SNOW, PACKED_SNOW, ICE]
                        if x > 0:
                            has_snow_nearby = has_snow_nearby or grid[y-1, x-1] in [SNOW, PACKED_SNOW, ICE]
                        if x < WIDTH-1:
                            has_snow_nearby = has_snow_nearby or grid[y-1, x+1] in [SNOW, PACKED_SNOW, ICE]
                    
                    if has_snow_nearby:
                        # If there's snow nearby, ensure we stay in place
                        grid[y, x] = SNOW_FLAKES
                        continue
                elif grid[y, x] == SNOW:
                    if random.random() < 0.8:  # 80% chance to stay still per rules
                        continue
                elif grid[y, x] == PACKED_SNOW:
                    if random.random() < 0.95:  # 95% chance to stay still per rules
                        continue
                elif grid[y, x] == ICE:
                    if random.random() < 0.99:  # 99% chance to stay still per rules
                        continue
                    
                # Check if snowflake is beyond the extended bounds
                if x <= 0 or x >= WIDTH-1:
                    grid[y, x] = EMPTY
                    snowflake_chars[y, x] = 0
                    snowflake_speeds[y, x] = 1.0
                    continue

                # Possible movement directions with weights
                moves = []
                
                # Check if we're at the bottom row and in floor area
                at_floor = (y == HEIGHT-2 and 
                          x >= FLOOR_START and 
                          x < FLOOR_START + FLOOR_WIDTH)
                
                # Apply wind effect to movement probabilities
                wind_effect = wind_strength * (1.0 if grid[y, x] == SNOW_FLAKES else 0.3)
                
                # Different movement weights based on particle type
                if grid[y, x] == SNOW_FLAKES:
                    # Snow flakes affected by wind
                    if not at_floor:
                        # Ensure no snow-type blocks in potential movement directions
                        can_move_down = y < HEIGHT-1 and grid[y+1, x] == EMPTY
                        can_move_left = x > 0 and y < HEIGHT-1 and grid[y+1, x-1] == EMPTY
                        can_move_right = x < WIDTH-1 and y < HEIGHT-1 and grid[y+1, x+1] == EMPTY
                        
                        if can_move_down:
                            moves.append((y+1, x, 0.8))  # Base downward probability
                        
                        # Diagonal movement affected by wind
                        left_prob = 0.1 - wind_effect
                        right_prob = 0.1 + wind_effect
                        
                        if can_move_left and left_prob > 0:
                            moves.append((y+1, x-1, left_prob))
                        if can_move_right and right_prob > 0:
                            moves.append((y+1, x+1, right_prob))
                            
                        # Horizontal movement based on wind
                        if wind_strength < 0 and x > 0 and grid[y, x-1] == EMPTY:
                            moves.append((y, x-1, abs(wind_effect) * 0.5))
                        if wind_strength > 0 and x < WIDTH-1 and grid[y, x+1] == EMPTY:
                            moves.append((y, x+1, abs(wind_effect) * 0.5))
                else:
                    # Snow and packed snow have more restricted movement
                    if not at_floor and y < HEIGHT-1:
                        if grid[y+1, x] == EMPTY:
                            moves.append((y+1, x, 0.9))  # Mostly straight down
                        if x > 0 and grid[y+1, x-1] == EMPTY:
                            moves.append((y+1, x-1, 0.05))  # Rare diagonal
                        if x < WIDTH-1 and grid[y+1, x+1] == EMPTY:
                            moves.append((y+1, x+1, 0.05))  # Rare diagonal
                
                # If we have possible moves, choose one based on weights
                if moves:
                    # Extract probabilities
                    probs = [m[2] for m in moves]
                    # Normalize probabilities
                    total = sum(probs)
                    probs = [p/total for p in probs]
                    
                    # Choose a move
                    choice = random.choices(moves, weights=probs, k=1)[0]
                    new_y, new_x, _ = choice
                    
                    # Move the particle
                    grid[new_y, new_x] = grid[y, x]  # Preserve particle type
                    snowflake_chars[new_y, new_x] = snowflake_chars[y, x]
                    snowflake_speeds[new_y, new_x] = snowflake_speeds[y, x]
                    flake_existence_time[new_y, new_x] = flake_existence_time[y, x]
                    grid[y, x] = EMPTY
                    snowflake_chars[y, x] = 0
                    snowflake_speeds[y, x] = 1.0
                    flake_existence_time[y, x] = 0

def physics_loop():
    """Continuous physics updates."""
    global running
    while running:
        spawn_snowflakes()
        update_wind()
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
    global running, snowing, current_spawn_rate, wind_strength, target_wind_strength, temperature
    running = True
    
    # Set up signal handler
    signal.signal(signal.SIGINT, handle_exit)
    
    # Start physics thread
    physics_thread = Thread(target=physics_loop)
    physics_thread.daemon = True
    physics_thread.start()
    
    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        update_dimensions()
        clear_screen()
        
        # Track key states
        left_pressed = False
        right_pressed = False
        
        while running:
            key = term.inkey(timeout=0.01)
            
            if key == 'q':
                running = False
                break
            elif key == ' ':  # Space to toggle snow
                snowing = not snowing
            elif key.name == 'KEY_UP':  # Up arrow to increase spawn rate
                current_spawn_rate = min(current_spawn_rate + SPAWN_RATE_STEP, MAX_SPAWN_RATE)
            elif key.name == 'KEY_DOWN':  # Down arrow to decrease spawn rate
                current_spawn_rate = max(current_spawn_rate - SPAWN_RATE_STEP, MIN_SPAWN_RATE)
            elif key.name == 'KEY_LEFT':  # Left arrow for wind
                target_wind_strength = -MAX_WIND_STRENGTH * random.uniform(0.7, 1.0)
            elif key.name == 'KEY_RIGHT':  # Right arrow for wind
                target_wind_strength = MAX_WIND_STRENGTH * random.uniform(0.7, 1.0)
            elif key.name in ['KEY_LEFT_RELEASE', 'KEY_RIGHT_RELEASE']:  # Release wind keys
                target_wind_strength = 0
            elif key == '+' or key == '=':  # Increase temperature
                temperature = min(temperature + 1, 10)
            elif key == '-' or key == '_':  # Decrease temperature
                temperature = max(temperature - 1, -10)
            
            render_grid()
    
    print(term.normal)

if __name__ == '__main__':
    main()
