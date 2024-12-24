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

    def update_status_display(self, state):
        """Update the status display in the grid's background layer."""
        # Get status text components
        status = "ON" if state['snowing'] else "OFF"
        spawn_rate_percent = int(state['current_spawn_rate'] * 100)
        
        # Show wind direction with arrows
        if state['wind_strength'] < 0:
            wind_indicator = f"← Wind: {abs(int(state['wind_strength'] * 100))}%"
        elif state['wind_strength'] > 0:
            wind_indicator = f"Wind: {abs(int(state['wind_strength'] * 100))}% →"
        else:
            wind_indicator = "Wind: 0%"
            
        status_text = (f"Q: Quit | SPACE: Toggle Snow [{status}] | "
                      f"↑/↓: Adjust Spawn Rate ({spawn_rate_percent}%) | "
                      f"←/→: Wind | +/-: Temp ({state['temperature']}) | "
                      f"{wind_indicator} | "
                      f"H: Toggle Help | "
                      f"Click: Add/Remove Snow")

        # Calculate position based on config
        x_pos = int((config.STATUS_DISPLAY['x'] / 100.0) * self.grid.visible_width) + self.grid.visible_start
        y_pos = int((config.STATUS_DISPLAY['y'] / 100.0) * self.grid.height)

        # Clear previous status line
        for x in range(self.grid.width):
            self.grid.set_background(y_pos, x, ' ')

        # Set new status text in background layer
        for i, char in enumerate(status_text):
            if x_pos + i < self.grid.width:
                self.grid.set_background(y_pos, x_pos + i, char, config.STATUS_DISPLAY['color'])

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_str = hex(hex_color)[2:].zfill(6)  # Remove '0x' prefix and pad to 6 digits
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

    def render_grid(self, state, show_status=False):
        """Render the current state of the grid."""
        self.grid.update_dimensions()
        
        # Update or clear status in background layer
        if show_status:
            self.update_status_display(state)
        else:
            # Clear status line
            y_pos = int((config.STATUS_DISPLAY['y'] / 100.0) * self.grid.height)
            for x in range(self.grid.width):
                self.grid.set_background(y_pos, x, ' ')
            
        output = []
        
        # Render the visible portion of the grid
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
        
        # Write the final output
        sys.stdout.write(self.term.home + ''.join(output))
        sys.stdout.flush()
