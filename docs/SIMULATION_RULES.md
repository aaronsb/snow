# Snow Simulation Rules

## Particle Types

### Snow Flakes (❄/❅/❆/*)
- Most basic falling particle with variable mass (0.5 to 2.0)
- Lighter flakes are more affected by wind and fall slower
- Movement influenced by:
  - Mass (affects falling speed and wind resistance)
  - Wind strength (causes horizontal drift)
  - 60-80% chance to fall straight down (higher for heavier flakes)
  - 10% base chance for diagonal movement (adjusted by wind)
- Transforms to snow when:
  - Surrounded by 3 or more snow/packed/ice particles
  - Has sufficient support below (floor or existing snow)
  - Stationary for 4-15 frames (faster when supported)
- Compression occurs immediately when below snow/packed/ice

### Snow (░)
- Formed from accumulated snowflakes
- More stable than flakes with reduced wind effect (30% of full strength)
- Movement:
  - 80% chance to remain stationary
  - 90% chance for straight down when moving
  - 5% chance each for diagonal movement
- Transforms to packed snow when:
  - 7+ surrounding snow/packed particles OR 4+ snow depth below
  - Must have snow/packed/ice support below
  - Stationary time varies with snow coverage (base: 1000 frames)
- Compresses snowflakes below it

### Packed Snow (▒)
- Formed from compressed snow
- Very stable with minimal wind effect
- Movement:
  - 95% chance to remain stationary
  - 90% chance straight down when moving
  - 5% chance each for diagonal movement
- Transforms to ice when:
  - 8+ surrounding packed/ice particles OR 5+ packed depth below
  - Must have packed/ice support below
  - Stationary time varies with snow coverage (base: 2000 frames)

### Ice (▓)
- Final form after packed snow compression
- Most stable particle type
- Movement:
  - 99% chance to remain stationary
  - 90% chance straight down when moving
  - 5% chance each for diagonal movement
- Extremely resistant to melting

## Dynamic Accumulation Control

The simulation uses a dynamic backoff system to control snow accumulation:

- Monitors snow coverage relative to screen height
- Target coverage is bottom third of visible area
- When exceeding target:
  - Transformation times increase exponentially
  - Up to 9x slower at maximum coverage
  - Helps prevent overwhelming accumulation
  - Creates more natural-looking snowbanks

## Wind System

Wind mechanics are sophisticated and particle-dependent:

- Wind strength varies from -1 (left) to 1 (right)
- Changes gradually with 0.05 ramp speed
- Duration varies randomly between 0.5-2.0 seconds
- Particle-specific effects:
  - Snowflakes: Full wind effect, scaled by mass
  - Snow: 30% of wind strength
  - Packed/Ice: Minimal wind effect
- Affects both horizontal drift and diagonal movement

## Simulation Parameters

### Spawning
- Sparse snowfall with 10% spawn chance per position
- Spawns across multiple random positions in visible area
- Limited by maximum snowflake count (200, adjustable 100-2000)
- Lower limits create more gradual accumulation

### Physics
- Base gravity delay: 0.05 seconds
- Individual snowflake speeds vary between 30-70% of base speed (to keep flakes light)
- Particles track stationary time for transformations

## Temperature and Melting System

Temperature affects melting exponentially:

- Base melt chance: 0.02 (2%)
- Modified by temperature exponentially: chance * (2^(temp/2))
- Melting restrictions:
  - Requires adjacent empty space or snowflakes
  - Cannot melt at floor boundary
- Particle-specific melting behavior:
  - Snowflakes: Always evaporate
  - Snow: 20% chance to compress to packed, 20% chance to evaporate
  - Packed Snow: 20% chance to compress to ice, 5% chance to evaporate
  - Ice: 1% chance to evaporate

### Wind Mechanics
- Wind strength ranges from -1 (left) to 1 (right)
- Maximum wind force of 0.8
- Gradual wind changes with 0.05 ramp speed
- Affects snowflakes more than solid particles
- Snow flakes:
  - Full wind effect on movement
  - Can drift horizontally based on wind strength
- Snow/Packed Snow:
  - Reduced wind effect (30% of full strength)
  - Limited horizontal movement

### Floor Mechanics
- Solid floor exists in central portion of simulation
- Particles accumulate on floor
- Floor width extends 25% beyond visible area on each side

## Background Sprites

### Sprite Properties
- Position (x,y): Percentage-based positioning relative to visible area
- Z-order: Depth from 0 (front) to 255 (back), snow scene is at 127
- Color: Various coloring methods including solid, RGB range, and HSL ramp
- Scaling:
  - scale_x: Horizontal scale percentage (100 = original size, 200 = double width)
  - scale_y: Vertical scale percentage (100 = original size, 200 = double height)
  - Scales from upper left origin using nearest neighbor interpolation
  - Defaults to 100% if not specified
  - Can be set independently for width/height stretching effects

### Sprite Layering
- Background sprites are rendered behind snow (z > 127)
- Multiple sprites can overlap based on z-order
- Transparency supported through space characters

### Boundary Handling
- Simulation extends 50% beyond visible area
- Particles are removed if they reach horizontal boundaries
- Bottom row cleared outside visible area when near capacity (95% full)
