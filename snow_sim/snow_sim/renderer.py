"""Terminal renderer for snow simulation."""
import sys
from . import config

class Renderer:
    def __init__(self, grid):
        """Initialize renderer with grid reference."""
        self.grid = grid
        self.term = config.term

    def clear_screen(self):
        """Clear the terminal screen."""
        print(self.term.home + self.term.clear)

    def get_status_line(self, state):
        """Generate the status line with current simulation state."""
        status = "ON" if state['snowing'] else "OFF"
        spawn_rate_percent = int(state['current_spawn_rate'] * 100)
        
        # Show wind direction with arrows
        if state['wind_strength'] < 0:
            wind_indicator = f"← Wind: {abs(int(state['wind_strength'] * 100))}%"
        elif state['wind_strength'] > 0:
            wind_indicator = f"Wind: {abs(int(state['wind_strength'] * 100))}% →"
        else:
            wind_indicator = "No Wind"
            
        return (self.term.white + 
                f"Q: Quit | SPACE: Toggle Snow [{status}] | "
                f"↑/↓: Adjust Spawn Rate ({spawn_rate_percent}%) | "
                f"←/→: Wind | +/-: Temp ({state['temperature']}) | "
                f"{wind_indicator} | "
                f"Click: Add/Remove Snow\n\n")

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_str = hex(hex_color)[2:].zfill(6)  # Remove '0x' prefix and pad to 6 digits
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def render_grid(self, state):
        """Render the current state of the grid."""
        self.grid.update_dimensions()
        output = []
        
        # Add status line
        output.append(self.get_status_line(state))
        
        # Only render the visible portion
        for y in range(self.grid.height):
            for x in range(self.grid.visible_start, 
                         self.grid.visible_start + self.grid.visible_width):
                char, color = self.grid.get_display_char(y, x)
                if color is not None:
                    r, g, b = self.hex_to_rgb(color)
                    output.append(self.term.color_rgb(r, g, b) + char)
                else:
                    output.append(self.term.white + char)
            output.append('\n')
        
        sys.stdout.write(self.term.home + ''.join(output))
        sys.stdout.flush()
