# DSI Examples

This directory contains example scripts demonstrating how to use the Digital Signal Intelligence pricing models.

## Available Examples

### 1. Cyber Insurance Pricing (`example_cyber_pricing.py`)

Demonstrates the cyber insurance pricing model with three scenarios:
- **Example 1**: Secure technology company with strong security posture
- **Example 2**: Healthcare company with security vulnerabilities
- **Example 3**: Batch pricing for multiple companies

**Run:**
```bash
python examples/example_cyber_pricing.py
```

### 2. API Client (`example_api_client.py`)

Shows how to interact with the DSI REST API:
- Health checks
- Getting quotes via API
- Batch processing

**Prerequisites:**
Start the API server first:
```bash
python -m api.server
# or
docker-compose up
```

**Run:**
```bash
python examples/example_api_client.py
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run examples directly:**
   ```bash
   python examples/example_cyber_pricing.py
   ```

3. **For API examples, start the server:**
   ```bash
   # Terminal 1: Start API
   python -m api.server

   # Terminal 2: Run examples
   python examples/example_api_client.py
   ```

## Example Output

The examples will show:
- Composite risk scores (0-1000)
- Risk tier assignments (Tier 1-5)
- Annual premium calculations
- Recommended coverage limits
- Breach/loss probabilities
- Actionable recommendations for risk mitigation

## Customization

Each example can be modified to test different scenarios:
- Change signal values to simulate different security postures
- Adjust company profiles (revenue, employees, industry)
- Test different coverage types
- Experiment with various risk factors

## Additional Resources

- **API Documentation**: http://localhost:5000/docs (when server is running)
- **Model READMEs**: See `/models/*/README.md` for detailed model documentation
- **Test Files**: See `/models/*/tests/` for more usage examples
