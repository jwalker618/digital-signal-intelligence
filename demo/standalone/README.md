# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A new method of Technical Pricing in Insurance

| Item | Value |
|-|-|
|Version|0.3.0|
|Date|January 2025|
|Classification|demonstration|

---

# Standalone HTML Demos

Interactive HTML demonstrations that work directly in any web browser without requiring Python or a server installation.

## Available Demos

| Demo | Description | Use Case |
|------|-------------|----------|
| `index.html` | Portal to all standalone demos | Starting point |
| `signal-scoring.html` | Interactive signal weight exploration | Learn how signals contribute to scores |
| `tier-visualization.html` | Score-to-tier mapping | Understand tier boundaries |
| `pricing-calculator.html` | Premium calculation with ILF curves | Explore pricing mechanics |
| `workflow-animation.html` | Animated 14-step workflow | Understand DSI workflow |
| `coverage-comparison.html` | Compare all 7 coverage types | See signal weight differences |

## Usage

Simply open any `.html` file directly in your web browser:

```bash
# macOS
open index.html

# Linux
xdg-open index.html

# Windows
start index.html
```

Or navigate to the file in your file browser and double-click it.

## Features

- **No installation required** - Works in any modern web browser
- **Interactive controls** - Sliders, inputs, and visualizations
- **Educational** - Designed to teach DSI concepts
- **Self-contained** - All CSS/JS inline (no external dependencies)

## Technical Notes

- Demos use simulated data and calculations
- All demos are self-contained HTML files
- Uses Chart.js for visualizations (loaded from CDN)

## Related

- `/demo/server.py` - Live demo server with actual workflow
- `/demo/legacy/` - Polished dashboard interfaces
