# Snow Simulation Rules

## Particle Types

### Snow Flakes (❄/❅/❆/*)
- Most basic falling particle
- Can transform into snow when accumulated
- Very light and easily disturbed by wind
- Has variable falling speeds
- Can move diagonally and drift horizontally
- Essentially incapable of affecting snow, packed snow, or ice
- If sufficient number of flakes are in proximity of another flake, they convert to a single snow particle
- If single flakes remain long enough, they will join a nearby snow, packed snow, or ice particle
- Immediately compressed (deleted) when below a snow block, simulating snow's weight

### Snow (░)
- Formed from accumulated snow flakes
- More stable than flakes but still affected by wind
- Can transform into packed snow, given sufficient time
- Has variable movement (20% chance, moreso on steep slopes)
- Heavier than snow flakes - compresses (deletes) any flakes directly below it

### Packed Snow (▒)
- Formed from accumulated snow
- More stable than regular snow
- Can transform into ice
- Has limited movement (5% chance to move)

### Ice (▓)
- Final form after packed snow compression
- Most stable particle type
- Extremely limited movement (1% chance to move)

## Movement Rules

### Snow Flakes
- Extremely light and fluid movement
- Stick in place once touching or their velocity is nearly stationary
- Individual speeds vary between 30-70% of base speed
- Focused downward movement:
  - Straight down (80% chance if space available)
  - Diagonal down-left/right (10% chance each if space available)


### Snow
- More solid and restricted movement
- 80% chance to remain stationary
- When moving:
  - Mostly straight down (90% chance if space available)
  - Rare diagonal movement (5% chance each direction if space available)

### Packed Snow
- 95% chance to remain stationary
- When moving:
  - Mostly straight down (90% chance if space available)
  - Rare diagonal movement (5% chance each direction if space available)
  - No horizontal drift

### Ice
- 99% chance to remain stationary
- When moving:
  - Mostly straight down (90% chance if space available)
  - Rare diagonal movement (5% chance each direction if space available)
  - No horizontal drift

## Transformation Rules

### Snow Flakes to Snow
- Neighbor-based conversion:
  - Requires 6 or more snow flakes in surrounding area (3x3 grid)
  - Immediately converts when touching existing snow
  - Creates extremely gradual accumulation

### Snow to Packed Snow
- Neighbor-based conversion:
  - Requires 7 or more snow/packed particles in surrounding area
  - Must be stationary for 1000 frames
  - Must have snow/packed/ice below
  - High density and time requirements ensure very slow accumulation

### Packed Snow to Ice
- Neighbor-based conversion:
  - Requires 8 or more packed/ice particles in surrounding area
  - Must be stationary for 2000 frames
  - Must have packed/ice below
  - Extreme requirements make ice formation very rare

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

## Environmental Rules

### Floor Mechanics
- Solid floor exists in central portion of simulation
- Particles accumulate on floor
- Floor width extends 25% beyond visible area on each side

### Boundary Handling
- Simulation extends 50 % beyond visible area
- Particles are removed if they reach horizontal boundaries
- Bottom row cleared outside visible area when near capacity (95% full)
