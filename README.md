# Snow Simulation

A Python-based particle simulation that creates realistic snow accumulation and transformation effects. The simulation models different states of snow (snowflakes, snow, packed snow, and ice) with realistic physics and environmental interactions.

![Snow Simulation](../screenshot.png)

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
git clone https://github.com/yourusername/snow-sim.git
cd snow-sim
```

2. Install the package:
```bash
pip install -e .
```

## Usage

Run the simulation:
```bash
python -m snow_sim
```

## Documentation

- [Simulation Rules](snow_sim/snow_sim/docs/SIMULATION_RULES.md) - Detailed explanation of particle behaviors and physics
- [Configuration](snow_sim/snow_sim/config.yaml) - Simulation parameters and settings

## Requirements

- Python 3.8+
- Dependencies are listed in setup.py
