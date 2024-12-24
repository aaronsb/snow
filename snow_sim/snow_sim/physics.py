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
            
        # Count nearby snow and snow flakes
        snow_neighbors = 0
        flake_neighbors = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
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
        threshold = 4  # Lower default threshold
        if has_support:
            threshold = 3  # Even easier when supported
        if snow_neighbors >= 2:
            threshold = 2  # Very easy when surrounded by snow
            
        # Adjust stationary time requirement
        required_time = 15  # Lower default time
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
            
        # Reduce stationary time requirement
        if self.grid.get_stationary_time(y, x) <= 100:  # Was 1000
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
        if ((snow_count >= 5 or depth >= 2) and 
            below in [config.SNOW, config.PACKED_SNOW, config.ICE]):
            self.grid.set_cell(y, x, config.PACKED_SNOW)
            return True
        return False

    def handle_ice_formation(self, y, x):
        """Handle formation of ice from packed snow."""
        if self.grid.get_cell(y, x) != config.PACKED_SNOW:
            return False
            
        # Reduce stationary time requirement
        if self.grid.get_stationary_time(y, x) <= 200:  # Was 2000
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
        if ((packed_count >= 6 or depth >= 3) and 
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
            if random.random() < 0.4:  # 40% chance to compress (was 20%)
                self.grid.set_cell(y, x, config.PACKED_SNOW)
            elif random.random() < 0.2:  # 20% chance to evaporate (was 80%)
                self.grid.set_cell(y, x, config.EMPTY)
        elif cell_type == config.PACKED_SNOW:
            if random.random() < 0.5:  # 50% chance to compress to ice (was 30%)
                self.grid.set_cell(y, x, config.ICE)
            elif random.random() < 0.05:  # 5% chance to evaporate (was 10%)
                self.grid.set_cell(y, x, config.EMPTY)
        elif cell_type == config.ICE:
            if random.random() < 0.02:  # 2% chance to melt away (was 5%)
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
