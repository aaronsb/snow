"""Configuration settings for the snow simulation."""
import os
import yaml
import blessed

term = blessed.Terminal()

def load_config():
    """Load configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Load configuration
_config = load_config()

# Export configuration values
SNOW_FLAKES = _config['particles']['snow_flakes']
SNOW = _config['particles']['snow']
PACKED_SNOW = _config['particles']['packed_snow']
ICE = _config['particles']['ice']
EMPTY = _config['particles']['empty']

# Simulation parameters
MELT_CHANCE = _config['physics']['melt_chance']
MAX_WIND_STRENGTH = _config['physics']['max_wind_strength']
WIND_RAMP_SPEED = _config['physics']['wind_ramp_speed']
BASE_MELT_CHANCE = _config['physics']['base_melt_chance']
GRAVITY_DELAY = _config['physics']['gravity_delay']
MAX_SNOWFLAKES_LIMIT = _config['simulation']['max_snowflakes']
MIN_SPAWN_RATE = _config['simulation']['min_spawn_rate']
MAX_SPAWN_RATE = _config['simulation']['max_spawn_rate']
SPAWN_RATE_STEP = _config['simulation']['spawn_rate_step']

# Visual settings
import colorsys
import random

def _generate_background_color(color_method, rel_x=0.0, rel_y=0.0):
    """Generate a color based on the specified method and relative position (0-1)."""
    if isinstance(color_method, int):  # Handle legacy solid color format
        return color_method
        
    method = color_method.get('method')
    direction = color_method.get('direction', 'horizontal')
    # Use x or y position based on direction
    position = rel_x if direction == 'horizontal' else rel_y
        
    if method == 'single_channel':
        channel = color_method.get('channel', 'all')
        min_val = color_method.get('min', 170)
        max_val = color_method.get('max', 255)
        
        # Use position to interpolate between min and max
        value = int(min_val + (max_val - min_val) * position)
        
        if channel == 'all':  # Grayscale
            return (value << 16) | (value << 8) | value
        elif channel == 'r':
            return value << 16
        elif channel == 'g':
            return value << 8
        elif channel == 'b':
            return value
            
    elif method == 'rgb_range':
        min_color = color_method.get('min', 0xaaaaaa)
        max_color = color_method.get('max', 0xffffff)
        
        # Extract RGB components
        min_r = (min_color >> 16) & 0xFF
        min_g = (min_color >> 8) & 0xFF
        min_b = min_color & 0xFF
        max_r = (max_color >> 16) & 0xFF
        max_g = (max_color >> 8) & 0xFF
        max_b = max_color & 0xFF
        
        # Interpolate each component
        r = int(min_r + (max_r - min_r) * position)
        g = int(min_g + (max_g - min_g) * position)
        b = int(min_b + (max_b - min_b) * position)
        
        return (r << 16) | (g << 8) | b
        
    elif method == 'hsl_ramp':
        hue_start = color_method.get('hue_start', 200)
        hue_end = color_method.get('hue_end', 240)
        saturation = color_method.get('saturation', 100)
        lightness_min = color_method.get('lightness_min', 70)
        lightness_max = color_method.get('lightness_max', 90)
        
        # Interpolate hue based on position
        hue = (hue_start + (hue_end - hue_start) * position) / 360.0
        sat = saturation / 100.0
        
        # Can also interpolate lightness if specified
        light = (lightness_min + (lightness_max - lightness_min) * position) / 100.0
        
        r, g, b = colorsys.hls_to_rgb(hue, light, sat)
        return (int(r * 255) << 16) | (int(g * 255) << 8) | int(b * 255)
        
    return 0xffffff  # Default to white if method is invalid


# Load sprites from config
SPRITES = _config.get('sprites', {})

# Process background images from config
BACKGROUND_IMAGES = []
for img in _config['visual'].get('background_images', []):
    processed_img = img.copy()
    # Store the color method for dynamic generation
    processed_img['color_method'] = processed_img.get('color')
    # Set initial color to None - will be generated per position
    processed_img['color'] = None
    BACKGROUND_IMAGES.append(processed_img)

# Status display configuration
STATUS_DISPLAY = _config['visual'].get('status_display', {
    'x': 0,
    'y': 0,
    'color': 0xffffff  # Default to white if not specified
})

def _generate_single_channel_color():
    """Generate a color using the single channel configuration."""
    channel_config = _config['visual']['snowflake_colors']['single_channel']
    value = random.randint(channel_config['min'], channel_config['max'])
    
    if channel_config['channel'] == 'all':  # Grayscale
        return (value << 16) | (value << 8) | value
    elif channel_config['channel'] == 'r':
        return value << 16
    elif channel_config['channel'] == 'g':
        return value << 8
    elif channel_config['channel'] == 'b':
        return value

def _generate_rgb_range_color():
    """Generate a color using the RGB range configuration."""
    rgb_config = _config['visual']['snowflake_colors']['rgb_range']
    return random.randint(rgb_config['min'], rgb_config['max'])

def _generate_hsl_ramp_color():
    """Generate a color using the HSL ramp configuration."""
    hsl_config = _config['visual']['snowflake_colors']['hsl_ramp']
    
    # Generate random hue between start and end
    hue = random.uniform(hsl_config['hue_start'], hsl_config['hue_end']) / 360.0
    saturation = hsl_config['saturation'] / 100.0
    lightness = random.uniform(
        hsl_config['lightness_min'], 
        hsl_config['lightness_max']
    ) / 100.0
    
    # Convert HSL to RGB
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
    
    # Convert to hex color
    return (int(r * 255) << 16) | (int(g * 255) << 8) | int(b * 255)

def generate_snowflake_color():
    """Generate a color based on the active color scheme."""
    color_scheme = _config['visual']['snowflake_colors']['color_scheme']
    
    if color_scheme == 'single_channel':
        return _generate_single_channel_color()
    elif color_scheme == 'rgb_range':
        return _generate_rgb_range_color()
    elif color_scheme == 'hsl_ramp':
        return _generate_hsl_ramp_color()
    else:
        raise ValueError(f"Unknown color scheme: {color_scheme}")

# Split snow chars and masses into separate lists for easier access
SNOW_CHARS = [char_data[0] for char_data in _config['visual']['snow_chars']]
SNOW_MASSES = [char_data[1] for char_data in _config['visual']['snow_chars']]
SNOW_CHAR = _config['visual']['snow_char']
PACKED_SNOW_CHAR = _config['visual']['packed_snow_char']
ICE_CHAR = _config['visual']['ice_char']

# Default simulation state
DEFAULT_STATE = _config['simulation']['default_state']

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
