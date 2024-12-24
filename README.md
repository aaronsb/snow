# Snow Simulation

A Python-based particle simulation that creates realistic snow accumulation and transformation effects. The simulation models different states of snow (snowflakes, snow, packed snow, and ice) with realistic physics and environmental interactions.

![Snow Simulation](screenshot.png)

## Features

- Multiple particle types with unique behaviors:
  - Snowflakes (❄/❅/❆/*) - Light, drifting particles
  - Snow (░) - Accumulated snow with moderate stability
  - Packed Snow (▒) - Compressed snow with increased stability
  - Ice (▓) - Final form with maximum stability

- Realistic environmental effects:
  - Temperature system affecting melting rates
  - Wind mechanics with variable strength and direction
  - Gravity-based movement with particle-specific behaviors
  - Natural compression and transformation systems

- Configurable simulation parameters:
  - Adjustable spawn rates and particle limits
  - Customizable physics settings
  - Temperature and wind control

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aaronsb/snow.git
cd snow
```

2. Install the package:
```bash
pip install -e .
```

## Usage

Run the simulation:
```bash
python -m snow
```

## Tips & Tricks

- **Building Snow Mountains**: 
  - Start with colder temperatures (below zero) to allow snow to accumulate faster
  - Once you have good accumulation, increase temperature to 0-2 to create a pleasing melting effect
  - This creates natural-looking snow mountain formations

- **Interactive Mountains**:
  - Click on the mountain backgrounds to modify their shape
  - Build custom landscapes to affect snow accumulation patterns

- **Wind Effects**:
  - Strong winds can blow snowflakes off mountains
  - Wind also causes snowflakes to clump together more quickly
  - Use wind strategically to shape snow formations

## Documentation

- [Simulation Rules](docs/SIMULATION_RULES.md) - Detailed explanation of particle behaviors and physics
- [Configuration](snow/config.yaml) - Simulation parameters and settings

## Requirements

- Python 3.8+
- Dependencies are listed in setup.py
