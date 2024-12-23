"""Physics engine for snow simulation."""
import random
from . import config

class Physics:
    def __init__(self, grid):
        """Initialize physics engine with grid reference."""
        self.grid = grid
        self.wind_strength = 0
        self.target_wind_strength = 0
        
    def update_wind(self):
        """Update wind strength based on target."""
        if self.wind_strength < self.target_wind_strength:
            self.wind_strength = min(self.wind_strength + config.WIND_RAMP_SPEED, self.target_wind_strength)
        elif self.wind_strength > self.target_wind_strength:
            self.wind_strength = max(self.wind_strength - config.WIND_RAMP_SPEED, self.target_wind_strength)

    def set_target_wind(self, target):
        """Set the target wind strength."""
        self.target_wind_strength = target

    def handle_compression(self, y, x):
        """Handle compression of particles."""
        if self.grid.get_cell(y, x) != config.SNOW_FLAKES:
            return False
            
        # Count nearby and above snow flakes
        flake_neighbors = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ny, nx = y + dy, x + dx
                if self.grid.get_cell(ny, nx) == config.SNOW_FLAKES:
                    flake_neighbors.append((ny, nx))
        
        # Convert if enough flakes and been still for longer
        if len(flake_neighbors) >= 6 and self.grid.get_stationary_time(y, x) > 20:
            # Remove the neighboring flakes that were "compressed"
            for ny, nx in flake_neighbors:
                self.grid.set_cell(ny, nx, config.EMPTY)
            # Convert center flake to snow
            self.grid.set_cell(y, x, config.SNOW)
            return True
        return False

    def handle_snow_packing(self, y, x):
        """Handle packing of snow into packed snow."""
        if self.grid.get_cell(y, x) != config.SNOW:
            return False
            
        if self.grid.get_stationary_time(y, x) <= 1000:
            return False
            
        # Count nearby snow
        snow_count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ny, nx = y + dy, x + dx
                cell = self.grid.get_cell(ny, nx)
                if cell in [config.SNOW, config.PACKED_SNOW]:
                    snow_count += 1
        
        # Convert if enough snow nearby and snow/packed below
        below = self.grid.get_cell(y+1, x)
        if snow_count >= 7 and below in [config.SNOW, config.PACKED_SNOW, config.ICE]:
            self.grid.set_cell(y, x, config.PACKED_SNOW)
            return True
        return False

    def handle_ice_formation(self, y, x):
        """Handle formation of ice from packed snow."""
        if self.grid.get_cell(y, x) != config.PACKED_SNOW:
            return False
            
        if self.grid.get_stationary_time(y, x) <= 2000:
            return False
            
        # Count nearby packed snow
        packed_count = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                ny, nx = y + dy, x + dx
                cell = self.grid.get_cell(ny, nx)
                if cell in [config.PACKED_SNOW, config.ICE]:
                    packed_count += 1
        
        # Convert if enough packed snow nearby and packed/ice below
        below = self.grid.get_cell(y+1, x)
        if packed_count >= 8 and below in [config.PACKED_SNOW, config.ICE]:
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
            if random.random() < 0.2:  # 20% chance to compress
                self.grid.set_cell(y, x, config.PACKED_SNOW)
            else:  # 80% chance to evaporate
                self.grid.set_cell(y, x, config.EMPTY)
        elif cell_type == config.PACKED_SNOW:
            if random.random() < 0.3:  # 30% chance to compress to ice
                self.grid.set_cell(y, x, config.ICE)
            elif random.random() < 0.1:  # 10% chance to evaporate
                self.grid.set_cell(y, x, config.EMPTY)
        elif cell_type == config.ICE:
            if random.random() < 0.05:  # 5% chance to melt away
                self.grid.set_cell(y, x, config.EMPTY)
        
        return True

    def calculate_movement(self, y, x):
        """Calculate possible movement directions for a particle."""
        cell_type = self.grid.get_cell(y, x)
        if cell_type == config.EMPTY:
            return None
            
        # Check if at floor
        if self.grid.is_at_floor(y, x):
            return None
            
        moves = []
        wind_effect = self.wind_strength * (1.0 if cell_type == config.SNOW_FLAKES else 0.3)
        
        if cell_type == config.SNOW_FLAKES:
            # Snow flakes affected by wind
            can_move_down = self.grid.get_cell(y+1, x) == config.EMPTY
            can_move_left = x > 0 and self.grid.get_cell(y+1, x-1) == config.EMPTY
            can_move_right = x < self.grid.width-1 and self.grid.get_cell(y+1, x+1) == config.EMPTY
            
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
            if wind_effect < 0 and x > 0 and self.grid.get_cell(y, x-1) == config.EMPTY:
                moves.append((y, x-1, abs(wind_effect) * 0.5))
            if wind_effect > 0 and x < self.grid.width-1 and self.grid.get_cell(y, x+1) == config.EMPTY:
                moves.append((y, x+1, abs(wind_effect) * 0.5))
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
