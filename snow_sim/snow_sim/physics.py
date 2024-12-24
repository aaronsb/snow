"""Physics engine for snow simulation."""
import random
import time
from . import config

class Physics:
    def __init__(self, grid):
        """Initialize physics engine with grid reference."""
        self.grid = grid
        self.wind_strength = 0
        self.target_wind_strength = 0
        self.wind_stop_time = 0
        self.base_snow_time = 1000  # Base time for snow packing
        self.base_ice_time = 2000   # Base time for ice formation
        self.current_backoff = 1.0  # Current backoff factor
        
    def calculate_backoff_factor(self):
        """Calculate new backoff factor based on snow coverage."""
        total_height = self.grid.height
        mid_height = total_height // 2
        
        # Count snow particles in each row
        snow_counts = [0] * total_height
        for y in range(total_height):
            for x in range(self.grid.width):
                cell = self.grid.get_cell(y, x)
                if cell in [config.SNOW, config.PACKED_SNOW, config.ICE]:
                    snow_counts[y] += 1
        
        # Find highest point with significant snow (>10% of width)
        threshold = self.grid.width * 0.1
        snow_height = 0
        for y in range(total_height):
            if snow_counts[y] > threshold:
                snow_height = total_height - y
                break
        
        # Calculate percentage of height covered relative to mid-height target
        coverage = snow_height / total_height if total_height > 0 else 0
        target_coverage = 0.33  # Target is bottom third of height
        
        # Calculate backoff factor (1.0 below target, increases exponentially as we exceed target)
        if coverage <= target_coverage:
            return 1.0
        else:
            # Exponential backoff starting at target coverage
            excess = (coverage - target_coverage) / target_coverage  # Normalized excess
            return 1.0 + (excess * excess * 8)  # Steeper quadratic increase up to 9x slower
        
    def update_wind(self):
        """Update wind strength based on target."""
        # Check if wind should stop
        if self.wind_stop_time and time.time() >= self.wind_stop_time:
            self.target_wind_strength = 0
            self.wind_stop_time = 0
            
        if self.wind_strength < self.target_wind_strength:
            self.wind_strength = min(self.wind_strength + config.WIND_RAMP_SPEED, self.target_wind_strength)
        elif self.wind_strength > self.target_wind_strength:
            self.wind_strength = max(self.wind_strength - config.WIND_RAMP_SPEED, self.target_wind_strength)

    def set_target_wind(self, target):
        """Set the target wind strength and schedule stop time."""
        self.target_wind_strength = target
        if target != 0:  # Only set timer when starting wind
            min_duration, max_duration = config._config['physics']['wind_duration_range']
            duration = random.uniform(min_duration, max_duration)
            self.wind_stop_time = time.time() + duration

    def handle_compression(self, y, x):
        """Handle compression of particles."""
        if self.grid.get_cell(y, x) != config.SNOW_FLAKES:
            return False
            
        # Check if at floor with snow above
        is_at_floor = self.grid.is_at_floor(y, x)
        if is_at_floor:
            above = self.grid.get_cell(y-1, x) if y > 0 else None
            if above in [config.SNOW, config.PACKED_SNOW, config.ICE]:
                self.grid.set_cell(y, x, config.SNOW)
                return True

        # Check adjacent cells (up, down, left, right)
        adjacent_snow = 0
        total_neighbors = 0
        for dy, dx in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # Left, right, up, down
            ny, nx = y + dy, x + dx
            cell = self.grid.get_cell(ny, nx)
            if cell is not None:  # If within bounds
                total_neighbors += 1
                if cell in [config.SNOW, config.PACKED_SNOW, config.ICE]:
                    adjacent_snow += 1

        # Convert immediately if surrounded on 3 or more sides
        if total_neighbors >= 3 and adjacent_snow >= 3:
            self.grid.set_cell(y, x, config.SNOW)
            return True

        # For non-surrounded cases, check diagonal neighbors too
        snow_neighbors = adjacent_snow
        flake_neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:  # Skip center
                    continue
                if dy in [-1, 1] and dx in [-1, 1]:  # Diagonal positions
                    ny, nx = y + dy, x + dx
                    cell = self.grid.get_cell(ny, nx)
                    if cell == config.SNOW_FLAKES:
                        flake_neighbors.append((ny, nx))
                    elif cell in [config.SNOW, config.PACKED_SNOW, config.ICE]:
                        snow_neighbors += 1

        # Check what's below
        is_on_floor = self.grid.is_at_floor(y, x)
        below = self.grid.get_cell(y+1, x) if y < self.grid.height-1 else None
        is_on_snow = below in [config.SNOW, config.PACKED_SNOW, config.ICE]
        has_support = is_on_floor or is_on_snow

        # Determine compression threshold based on conditions
        threshold = 4  # Default threshold
        if has_support:
            threshold = 3  # Easier when supported
        if snow_neighbors >= 2:
            threshold = 2  # Very easy when surrounded by snow

        # Adjust stationary time requirement
        required_time = 15  # Default time
        if has_support:
            required_time = 8  # Faster when supported
        if snow_neighbors >= 2:
            required_time = 4  # Very fast when surrounded by snow
            
        # Convert if conditions are met
        if len(flake_neighbors) >= threshold and self.grid.get_stationary_time(y, x) > required_time:
            # Convert center flake to snow
            self.grid.set_cell(y, x, config.SNOW)
            # Keep neighbors to help with buildup
            return True
        return False

    def handle_snow_packing(self, y, x):
        """Handle packing of snow into packed snow."""
        if self.grid.get_cell(y, x) != config.SNOW:
            return False
            
        # Apply current backoff factor to time requirement
        required_time = int(self.base_snow_time * self.current_backoff)
        
        # Check stationary time requirement
        if self.grid.get_stationary_time(y, x) <= required_time:
            return False
            
        # Count nearby snow
        snow_count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ny, nx = y + dy, x + dx
                cell = self.grid.get_cell(ny, nx)
                if cell in [config.SNOW, config.PACKED_SNOW]:
                    snow_count += 1
        
        # Check depth of snow column below
        depth = 0
        check_y = y + 1
        while check_y < self.grid.height:
            cell = self.grid.get_cell(check_y, x)
            if cell not in [config.SNOW, config.PACKED_SNOW]:
                break
            depth += 1
            check_y += 1
        
        # Check what's below
        below = self.grid.get_cell(y+1, x)
        
        # Convert if enough snow nearby or enough depth, and has support below
        if ((snow_count >= 7 or depth >= 4) and  # Increased requirements
            below in [config.SNOW, config.PACKED_SNOW, config.ICE]):
            self.grid.set_cell(y, x, config.PACKED_SNOW)
            return True
        return False

    def handle_ice_formation(self, y, x):
        """Handle formation of ice from packed snow."""
        if self.grid.get_cell(y, x) != config.PACKED_SNOW:
            return False
            
        # Apply current backoff factor to time requirement
        required_time = int(self.base_ice_time * self.current_backoff)
        
        # Check stationary time requirement
        if self.grid.get_stationary_time(y, x) <= required_time:
            return False
            
        # Count nearby packed snow
        packed_count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ny, nx = y + dy, x + dx
                cell = self.grid.get_cell(ny, nx)
                if cell in [config.PACKED_SNOW, config.ICE]:
                    packed_count += 1
        
        # Check depth of packed snow column below
        depth = 0
        check_y = y + 1
        while check_y < self.grid.height:
            cell = self.grid.get_cell(check_y, x)
            if cell not in [config.PACKED_SNOW, config.ICE]:
                break
            depth += 1
            check_y += 1
        
        # Check what's below
        below = self.grid.get_cell(y+1, x)
        
        # Convert if enough packed snow nearby or enough depth, and has support below
        if ((packed_count >= 8 or depth >= 5) and  # Increased requirements
            below in [config.PACKED_SNOW, config.ICE]):
            self.grid.set_cell(y, x, config.ICE)
            return True
        return False

    def handle_melting(self, y, x, temperature):
        """Handle melting of particles."""
        cell_type = self.grid.get_cell(y, x)
        if cell_type == config.EMPTY:
            return False
            
        # Calculate melt chance based on temperature
        melt_chance = config.BASE_MELT_CHANCE * (2 ** (temperature / 2))  # Exponential scaling
        
        if random.random() >= melt_chance:
            return False
            
        # Check if particle can melt/evaporate
        if self.grid.is_at_floor(y, x):
            return False
            
        can_melt = False
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ny, nx = y + dy, x + dx
                if self.grid.is_at_floor(ny, nx):
                    continue
                cell = self.grid.get_cell(ny, nx)
                if cell in [config.EMPTY, config.SNOW_FLAKES]:
                    can_melt = True
                    break
            if can_melt:
                break

        if not can_melt and cell_type != config.SNOW_FLAKES:
            return False

        if cell_type == config.SNOW_FLAKES:
            self.grid.set_cell(y, x, config.EMPTY)
        elif cell_type == config.SNOW:
            if random.random() < 0.2:  # Reduced from 40%
                self.grid.set_cell(y, x, config.PACKED_SNOW)
            elif random.random() < 0.2:  # Kept at 20%
                self.grid.set_cell(y, x, config.EMPTY)
        elif cell_type == config.PACKED_SNOW:
            if random.random() < 0.2:  # Reduced from 50%
                self.grid.set_cell(y, x, config.ICE)
            elif random.random() < 0.05:  # Kept at 5%
                self.grid.set_cell(y, x, config.EMPTY)
        elif cell_type == config.ICE:
            if random.random() < 0.01:  # Reduced from 2%
                self.grid.set_cell(y, x, config.EMPTY)
        
        return True

    def get_snowflake_mass(self, x, y):
        """Get the mass of a snowflake based on its character."""
        if self.grid.get_cell(y, x) != config.SNOW_FLAKES:
            return 1.0
        char = self.grid.get_display_char(y, x)
        try:
            idx = config.SNOW_CHARS.index(char)
            return config.SNOW_MASSES[idx]
        except ValueError:
            return 1.0  # Default mass if character not found

    def calculate_movement(self, y, x):
        """Calculate possible movement directions for a particle."""
        cell_type = self.grid.get_cell(y, x)
        if cell_type == config.EMPTY:
            return None
            
        # Check if at floor
        if self.grid.is_at_floor(y, x):
            return None
            
        moves = []
        mass = self.get_snowflake_mass(x, y)
        
        # Adjust wind effect based on mass (lighter particles affected more by wind)
        wind_multiplier = 1.0 / mass if cell_type == config.SNOW_FLAKES else 0.3
        wind_effect = self.wind_strength * wind_multiplier
        
        if cell_type == config.SNOW_FLAKES:
            # Snow flakes affected by wind and mass
            can_move_down = self.grid.get_cell(y+1, x) == config.EMPTY
            can_move_left = x > 0 and self.grid.get_cell(y+1, x-1) == config.EMPTY
            can_move_right = x < self.grid.width-1 and self.grid.get_cell(y+1, x+1) == config.EMPTY
            
            # Heavier particles fall faster (higher downward probability)
            if can_move_down:
                moves.append((y+1, x, 0.6 + (mass * 0.2)))  # Mass affects falling speed
            
            # Diagonal movement affected by wind and mass
            left_prob = (0.1 / mass) - wind_effect
            right_prob = (0.1 / mass) + wind_effect
            
            if can_move_left and left_prob > 0:
                moves.append((y+1, x-1, left_prob))
            if can_move_right and right_prob > 0:
                moves.append((y+1, x+1, right_prob))
                
            # Horizontal movement based on wind and mass
            wind_horizontal = abs(wind_effect) * (0.5 / mass)  # Lighter particles move more horizontally
            if wind_effect < 0 and x > 0 and self.grid.get_cell(y, x-1) == config.EMPTY:
                moves.append((y, x-1, wind_horizontal))
            if wind_effect > 0 and x < self.grid.width-1 and self.grid.get_cell(y, x+1) == config.EMPTY:
                moves.append((y, x+1, wind_horizontal))
        else:
            # Snow and packed snow have more restricted movement
            if y < self.grid.height-1:
                if self.grid.get_cell(y+1, x) == config.EMPTY:
                    moves.append((y+1, x, 0.9))  # Mostly straight down
                if x > 0 and self.grid.get_cell(y+1, x-1) == config.EMPTY:
                    moves.append((y+1, x-1, 0.05))  # Rare diagonal
                if x < self.grid.width-1 and self.grid.get_cell(y+1, x+1) == config.EMPTY:
                    moves.append((y+1, x+1, 0.05))  # Rare diagonal
        
        return moves

    def apply_movement(self, y, x, moves):
        """Apply movement to a particle based on calculated moves."""
        if not moves:
            return False
            
        # Extract probabilities
        probs = [m[2] for m in moves]
        # Normalize probabilities
        total = sum(probs)
        probs = [p/total for p in probs]
        
        # Choose a move
        choice = random.choices(moves, weights=probs, k=1)[0]
        new_y, new_x, _ = choice
        
        # Move the particle
        self.grid.move_cell(y, x, new_y, new_x)
        return True
