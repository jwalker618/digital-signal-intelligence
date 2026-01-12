# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|demonstration|

---
# Live Demo

An interactive demonstration of the Digital Signal Intelligence (DSI) platform that runs the **actual workflow engine** with stub extractors for realistic simulation.

## Overview

This demo provides a hands-on experience with DSI's risk assessment and pricing capabilities. Unlike static documentation, this demo:

- **Runs real code**: Executes the actual DSI workflow engine
- **Uses real configurations**: Loads production signal configurations for all 7 coverages
- **Generates realistic results**: Produces scores, tiers, decisions, and premiums
- **Demonstrates all features**: Shows signals, group scores, referral logic, and pricing

## Quick Start

### Prerequisites

```bash
# From the repository root
pip install fastapi uvicorn
```

### Running the Demo

```bash
# From the repository root
python -m demo.server
```

Then open **http://localhost:8080** in your browser.

## Demo Features

### 1. Live Assessment Tab

Run individual risk assessments in real-time:

- Enter any company name and domain
- Select from 7 coverage types
- Watch the workflow execute
- See detailed results including:
  - Composite risk score (0-1000)
  - Risk tier assignment (1-5)
  - Underwriting decision (Approve/Refer/Decline)
  - Recommended premium
  - Individual signal contributions
  - Group score breakdowns

### 2. Batch Simulation Tab

Demonstrate statistical properties:

- Run assessments on multiple sample companies
- View aggregate statistics
- See tier and decision distributions
- Compare processing times

### 3. Coverage Explorer Tab

Explore signal configurations:

- Browse all 7 coverage types
- See signal definitions and weights
- View tier thresholds
- Understand group structures

### 4. Architecture Tab

Learn how DSI works:

- 14-step workflow explanation
- Signal group descriptions
- Decision logic documentation
- Integration patterns

### 5. Statistics Tab

Monitor demo usage:

- Total assessments run
- Average processing time
- Tier distribution chart
- Decision distribution chart

## API Endpoints

The demo server exposes the following REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main demo page |
| `/api/info` | GET | Server info and statistics |
| `/api/coverages` | GET | List available coverages |
| `/api/coverage/{id}` | GET | Coverage configuration details |
| `/api/assess` | POST | Run live assessment |
| `/api/batch-assess` | POST | Run batch assessments |
| `/api/samples` | GET | Sample companies for testing |

### Example API Usage

```bash
# Get server info
curl http://localhost:8080/api/info

# Run an assessment
curl -X POST http://localhost:8080/api/assess \
  -H "Content-Type: application/json" \
  -d '{
    "entity_name": "Acme Technology Corp",
    "domain_hint": "acmetech.com",
    "coverage": "cyber"
  }'

# List coverages
curl http://localhost:8080/api/coverages
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_PORT` | `8080` | Server port |
| `DEMO_HOST` | `0.0.0.0` | Server host |

### Sample Companies

The demo includes pre-configured sample companies:

1. Acme Technology Corp (US) - Tech company
2. Global Financial Services (US) - Financial services
3. Pacific Energy Holdings (US) - Energy sector
4. Northern Airlines (US) - Aviation
5. Maritime Shipping Co (UK) - Marine
6. Tech Consulting Partners (US) - Professional services
7. European Industrial Group (DE) - Manufacturing
8. Asia Pacific Insurance (SG) - Insurance

## Understanding the Results

### Risk Scores

- **0-20**: Excellent risk profile
- **21-40**: Good risk profile
- **41-60**: Moderate risk
- **61-80**: Elevated risk
- **81-100**: High risk

### Tier System

| Tier | Score Range | Description |
|------|-------------|-------------|
| 1 | 0-20 | Preferred risk |
| 2 | 21-40 | Standard plus |
| 3 | 41-60 | Standard |
| 4 | 61-80 | Substandard |
| 5 | 81-100 | High risk |

### Decision Types

- **Approve**: Auto-bind eligible
- **Refer**: Requires underwriter review
- **Decline**: Does not meet criteria

### Signal Groups

Each coverage uses 3-5 signal groups:

- **Financial Health**: Revenue, profitability, leverage
- **Operational Risk**: Industry factors, complexity
- **Historical Claims**: Loss history, frequency
- **Governance**: Management quality, controls
- **Market Position**: Size, competition, trends

## Technical Details

### How It Works

1. **Demo Server** (`server.py`): FastAPI application that wraps the DSI workflow
2. **Demo UI** (`index.html`): Single-page application with interactive features
3. **Workflow Engine**: Actual DSI `run_assessment()` function
4. **Stub Extractors**: Simulated data extraction (production uses real APIs)

### Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Demo UI (index.html)                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │
│  │  Live   │ │  Batch  │ │Coverage │ │  Architecture   │ │
│  │ Assess  │ │  Sim    │ │Explorer │ │  & Statistics   │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────────┬────────┘ │
└───────┼──────────┼──────────┼─────────────────┼──────────┘
        │          │          │                 │
        ▼          ▼          ▼                 ▼
┌──────────────────────────────────────────────────────────┐
│                  Demo Server (server.py)                 │
│  ┌───────────┐  ┌────────────┐  ┌───────────────────┐    │
│  │   REST    │  │   State    │  │   Result          │    │
│  │   API     │  │   Tracking │  │   Formatting      │    │
│  └─────┬─────┘  └────────────┘  └───────────────────┘    │
└────────┼─────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│                DSI Workflow Engine                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Entity   │ │  Signal  │ │  Score   │ │ Decision │     │
│  │ Resolve  │ │ Extract  │ │ Compute  │ │  Logic   │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

1. User enters company info in UI
2. UI sends POST to `/api/assess`
3. Server creates workflow context
4. Workflow engine:
   - Resolves entity identity
   - Extracts signals (stub data)
   - Computes weighted scores
   - Applies tier logic
   - Determines decision
   - Calculates premium
5. Server formats result
6. UI displays breakdown

## Limitations

This demo uses **stub extractors** that generate simulated data:

- Signal values are randomly generated within realistic ranges
- Results will vary between runs for the same company
- Not suitable for actual underwriting decisions

For production use, integrate real data sources:
- Financial APIs (D&B, S&P, Bloomberg)
- Cyber intelligence (SecurityScorecard, BitSight)
- Claims databases
- Industry data providers

## Troubleshooting

### Server Won't Start

```bash
# Check port availability
lsof -i :8080

# Try alternative port
DEMO_PORT=9090 python -m demo.server
```

### Import Errors

```bash
# Ensure you're in the repository root
cd /path/to/digital-signal-intelligence

# Install dependencies
pip install -e .
pip install fastapi uvicorn
```

### CORS Issues

The demo server allows all origins by default. For production, configure proper CORS.

## Additional Demos

### Standalone HTML Demos (`/standalone`)

No-install interactive demos that work directly in your browser:

| Demo | Description |
|-|-|
| `index.html` | Portal to all standalone demos |
| `signal-scoring.html` | Interactive signal weight exploration |
| `tier-visualization.html` | Score-to-tier mapping |
| `pricing-calculator.html` | Premium calculation with ILF curves |
| `workflow-animation.html` | Animated 14-step workflow |
| `coverage-comparison.html` | Compare all 7 coverage types |

### Legacy Dashboards (`/legacy`)

Polished dashboard interfaces for presentations:

| Dashboard | Description |
|-|-|
| `dsi_demo_dashboard.html` | Signal-level analysis |
| `dsi_demo_workflow.html` | Workflow visualization |
| `dsi_portfolio_dashboard.html` | Portfolio management |

## Contributing

To extend the demo:

1. Add new tabs in `index.html`
2. Add API endpoints in `server.py`
3. Update this README

## License

Part of the DSI platform. See repository LICENSE for details.
