"""Configuration settings for the snow simulation."""
import blessed

term = blessed.Terminal()

# Particle types
SNOW_FLAKES = 1
SNOW = 2
PACKED_SNOW = 3
ICE = 4
EMPTY = 0

# Simulation parameters
MELT_CHANCE = 0.001  # Base chance for melting
MAX_WIND_STRENGTH = 0.8  # Maximum wind force
WIND_RAMP_SPEED = 0.05  # How quickly wind builds up/dies down
BASE_MELT_CHANCE = 0.001  # Base chance for melting
GRAVITY_DELAY = 0.05  # Base falling speed
MAX_SNOWFLAKES_LIMIT = 2000  # Maximum limit for total snowflakes
MIN_SPAWN_RATE = 0.01  # Minimum spawn chance (1%)
MAX_SPAWN_RATE = 0.5   # Maximum spawn chance (50%)
SPAWN_RATE_STEP = 0.05  # How much to adjust spawn rate by

# Visual settings
SNOW_CHARS = ['❄', '❅', '❆', '*', '+', '.', '⠋', '⠛', '⠟', '⠿', '⡿', '⣿']  # Different snowflake characters
SNOW_CHAR = '░'  # ASCII 176 for snow
PACKED_SNOW_CHAR = '▒'  # ASCII 177 for packed snow
ICE_CHAR = '▓'  # ASCII 178 for ice

# Grid dimensions
def get_dimensions():
    """Get current grid dimensions based on terminal size."""
    visible_width = term.width
    width = int(visible_width * 2.0)  # Extend simulation 50% on each side
    height = term.height - 3  # Account for instructions and bottom padding
    visible_start = int(visible_width * 0.5)  # Where visible portion starts
    floor_width = int(visible_width * 1.5)  # Floor extends 25% on each side
    floor_start = int(visible_width * 0.25)  # Where floor starts
    
    return {
        'width': width,
        'height': height,
        'visible_width': visible_width,
        'visible_start': visible_start,
        'floor_width': floor_width,
        'floor_start': floor_start
    }

# Default simulation state
DEFAULT_STATE = {
    'snowing': True,  # Start with snow enabled
    'current_spawn_rate': 0.1,  # Start with 10% spawn chance
    'wind_strength': 0,  # Current wind strength (-1 to 1, negative = left, positive = right)
    'target_wind_strength': 0,  # Wind strength we're ramping towards
    'temperature': 0  # Temperature affects melt chance (-10 to 10)
}
