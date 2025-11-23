# Website Discovery - Quick Start Guide

## 🚀 5-Minute Quick Start

### 1. Test the Module

```bash
# Navigate to repo root
cd /home/user/digital-signal-intelligence

# Run the examples
python models/website_discovery/examples/example_discovery.py
```

### 2. Simple Python Script

```python
# test_discovery.py
import sys
sys.path.insert(0, 'models')

from website_discovery import CorporateWebsiteDiscovery

# Initialize
discovery = CorporateWebsiteDiscovery()

# Test with your companies
companies = [
    "Marks and Spencer",
    "MS Amlin",
    "Brit"
]

print("Discovering corporate websites...")
for company in companies:
    result = discovery.discover(company, use_search=False)
    if result.success:
        print(f"✓ {company}: {result.best_match.url}")
        print(f"  Score: {result.best_match.confidence_score:.1f}/100")
    else:
        print(f"✗ {company}: No match found")
    print()
```

### 3. Run Tests

```bash
# Unit tests
pytest models/website_discovery/tests/ -v -s

# Specific company test
pytest models/website_discovery/tests/test_website_discovery.py::TestRealCompanyDiscovery::test_marks_and_spencer_discovery -v -s
```

## 📝 Expected Results

### Marks & Spencer
- **Expected URL**: `corporate.marksandspencer.com` or `marksandspencer.com`
- **Confidence**: 70-90%
- **Indicators**: investor relations, corporate, governance

### MS Amlin
- **Expected URL**: `msamlin.com`
- **Confidence**: 60-80%
- **Note**: May have fewer corporate indicators (Lloyd's syndicate)

### Brit
- **Expected URL**: `britinsurance.com` or `brit.com`
- **Confidence**: 60-80%
- **Note**: Short name may be challenging

## ⚙️ Configuration

### Without API Keys (Default)
Uses domain generation strategy only - works offline, no costs

### With API Keys (Enhanced)
```bash
export GOOGLE_API_KEY="your_key"
export GOOGLE_CX="your_cx_id"
```

Then use:
```python
result = discovery.discover(company, use_search=True)
```

## 🐛 Troubleshooting

**Issue**: "No candidates found"
**Fix**: Try with domain hint:
```python
result = discovery.discover("Company Name", domain_hint="company.com")
```

**Issue**: "Low confidence scores"
**Fix**: Website may not have corporate indicators. Review all candidates:
```python
for candidate in result.all_candidates:
    print(f"{candidate.url}: {candidate.confidence_score:.1f}")
```

**Issue**: "Timeout errors"
**Fix**: Increase timeout:
```python
discovery = CorporateWebsiteDiscovery(timeout=20)
```

## 📚 Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Review [examples/example_discovery.py](examples/example_discovery.py) for more use cases
3. Run the test suite to see real-world results
4. Integrate into your DSI pricing workflow

## 💡 Tips

- **Start without search**: Test domain generation first (faster, free)
- **Use caching**: Enable cache for repeated lookups
- **Batch processing**: Use `discover_batch()` for multiple companies
- **Domain hints**: Provide hints when you have partial information
- **Review candidates**: Don't rely solely on best match, review top 3-5

## 🎯 Common Use Cases

### Case 1: Single Company Lookup
```python
result = discovery.discover("Microsoft")
print(result.best_match.url)
```

### Case 2: Bulk Processing
```python
companies = load_companies_from_csv()
results = discovery.discover_batch(companies, delay=1.0)
```

### Case 3: Integration with Pricing
```python
# In your pricing workflow
result = discovery.discover(company_name)
if result.success:
    website_url = result.best_match.url
    signals = collect_signals(website_url)
    premium = calculate_premium(company_profile, signals)
```

---

Ready to discover corporate websites! 🎉
