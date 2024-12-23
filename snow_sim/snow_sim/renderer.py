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
                f"{wind_indicator}\n\n")

    def get_cell_char(self, cell_type, char_index=0):
        """Get the character representation for a cell type."""
        if cell_type == config.SNOW_FLAKES:
            return config.SNOW_CHARS[char_index]
        elif cell_type == config.SNOW:
            return config.SNOW_CHAR
        elif cell_type == config.PACKED_SNOW:
            return config.PACKED_SNOW_CHAR
        elif cell_type == config.ICE:
            return config.ICE_CHAR
        else:
            return ' '

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
                cell_type = self.grid.get_cell(y, x)
                char_index = self.grid.get_snowflake_char(y, x)
                output.append(self.term.white + self.get_cell_char(cell_type, char_index))
            output.append('\n')
        
        sys.stdout.write(self.term.home + ''.join(output))
        sys.stdout.flush()
