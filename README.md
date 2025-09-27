# ROIC Monte Carlo Analysis

Monte Carlo simulation for ROIC analysis with interactive web visualization.

## What it does

- Runs 10,000 Monte Carlo simulations of ROIC factors
- Performs linear regression analysis with standardized betas
- Interactive 2D/3D charts with regression lines/planes
- Real-time filtering and statistics

## Usage

```bash
# Run simulation
uv run python scripts/monte_carlo_roic.py

# View interactive page
open docs/index.html
```

## Files

- `scripts/monte_carlo_roic.py` - Monte Carlo simulation
- `docs/index.html` - Interactive visualization
- `data/` - Simulation results (CSV)
