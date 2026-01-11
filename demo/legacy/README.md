# Legacy DSI Dashboards

Interactive HTML dashboards for DSI visualization and analysis. These are standalone dashboards that can be opened directly in a web browser without requiring Python or a server.

## Available Dashboards

| Dashboard | Description | Use Case |
|-----------|-------------|----------|
| `dsi_demo_dashboard.html` | Signal-level analysis dashboard | Explore individual signal scores and contributions |
| `dsi_demo_workflow.html` | Workflow visualization dashboard | Understand the 14-step DSI workflow |
| `dsi_portfolio_dashboard.html` | Portfolio management interface | Analyze portfolio-level risk distribution |

## Usage

Simply open any `.html` file directly in your web browser:

```bash
# On macOS
open dsi_demo_dashboard.html

# On Linux
xdg-open dsi_demo_dashboard.html

# On Windows
start dsi_demo_dashboard.html
```

Or navigate to the file in your file browser and double-click it.

## Features

- **No installation required** - Works in any modern web browser
- **Interactive charts** - Powered by Chart.js
- **Responsive design** - Works on desktop and mobile
- **Dark theme** - Easy on the eyes

## Note

These dashboards use simulated data for demonstration purposes. For live assessments, use the main demo server:

```bash
python -m demo.server
# Then open http://localhost:8080
```

## Related

- `/demo/standalone/` - Newer interactive demo tools
- `/demo/server.py` - Live demo server with actual workflow
