# Signal Collection Module

**Intelligent web analysis for insurance pricing**

The Signal Collection Module extracts model-specific information from corporate websites and other online sources to inform insurance pricing decisions. It combines intelligent crawling, content extraction, and configurable analysis to identify relevant signals for different insurance models.

## 🎯 Overview

Different insurance models require different types of information:

- **Cyber Insurance**: Security incidents, IT leadership, blog posts about breaches
- **Financial Institutions**: Annual reports, financial metrics, regulatory filings
- **Energy Companies**: Safety incidents, ESG reports, environmental data

This module provides model-specific collectors that can be configured to extract exactly the information needed for each pricing model.

## ✨ Features

### Model-Specific Collectors

- **CyberSignalCollector**: Extracts security incidents, key IT hires, vulnerability disclosures
- **FinancialInstitutionSignalCollector**: Finds financial reports and extracts key metrics
- **EnergySignalCollector**: Identifies safety incidents and ESG information

### Intelligent Crawling

- Priority URL handling (crawl important pages first)
- Configurable depth and page limits
- Rate limiting and politeness
- Content-type aware processing

### Content Extraction

- PDF extraction with multiple fallback strategies
- HTML article extraction with date awareness
- Document type detection and routing
- Metadata extraction

### Configurable Analysis

- Custom keywords per model
- Time-based filtering (e.g., last 12 months)
- Relevance scoring
- Context extraction
- Pattern matching with regex

## 📦 Installation

The module is part of the Digital Signal Intelligence repository:

```bash
# Install dependencies
pip install -r requirements.txt

# Additional dependencies for signal collection
pip install beautifulsoup4 requests PyPDF2 pdfplumber lxml
```

## 🚀 Quick Start

### Cyber Insurance Example

```python
from signal_collection import CyberSignalCollector, CyberConfig

# Configure collector
config = CyberConfig(
    max_pages=15,
    max_depth=2,
    time_window_months=12  # Last 12 months
)

# Create collector
collector = CyberSignalCollector(config)

# Collect signals
result = collector.collect(
    company_name="Example Tech Corp",
    website_url="https://example-tech.com"
)

# Analyze results
if result.success:
    print(f"Found {len(result.signals)} signals")
    print(f"Crawled {result.pages_crawled} pages")

    # Review top signals
    for signal in sorted(result.signals,
                        key=lambda s: s.relevance_score,
                        reverse=True)[:5]:
        print(f"{signal.keyword}: {signal.context[:100]}")
        print(f"  Source: {signal.source_type}, Date: {signal.date}")
```

### Financial Institutions Example

```python
from signal_collection import FinancialInstitutionSignalCollector, FinancialConfig

# Configure for financial analysis
config = FinancialConfig(
    max_pages=20,
    max_depth=3,
    document_types=["Annual Report", "Integrated Report"]
)

# Create collector
collector = FinancialInstitutionSignalCollector(config)

# Collect signals
result = collector.collect(
    company_name="Example Bank",
    website_url="https://example-bank.com"
)

# Review findings
if result.success:
    print(f"Documents found: {len(result.documents_found)}")
    for doc in result.documents_found:
        print(f"  - {doc}")

    # Extract metrics from signals
    metrics = [s for s in result.signals if s.source_type == "report"]
    print(f"\nMetrics extracted: {len(metrics)}")
    for metric in metrics:
        print(f"  {metric.keyword}: {metric.context}")
```

### Energy Company Example

```python
from signal_collection import EnergySignalCollector, EnergyConfig

# Configure for energy analysis
config = EnergyConfig(
    max_pages=15,
    time_window_months=24,  # Last 2 years for safety data
    priority_urls=["/sustainability", "/safety", "/esg"]
)

# Create collector
collector = EnergySignalCollector(config)

# Collect signals
result = collector.collect(
    company_name="Example Energy Corp",
    website_url="https://example-energy.com"
)

# Review incidents
if result.success:
    incidents = [s for s in result.signals if s.source_type == "incident"]
    print(f"Incidents found: {len(incidents)}")
    for incident in incidents:
        print(f"  - {incident.keyword} on {incident.date}")
        print(f"    {incident.context[:150]}")
```

## ⚙️ Configuration

### Base Configuration

All collectors inherit from `CollectionConfig`:

```python
@dataclass
class CollectionConfig:
    max_pages: int = 50              # Maximum pages to crawl
    max_depth: int = 3               # Maximum crawl depth
    delay: float = 1.0               # Delay between requests (seconds)
    time_window_months: int = 12     # Time window for filtering
    priority_urls: List[str]         # URLs to prioritize
    document_types: List[str]        # Document types to find
    keywords: List[str]              # Keywords to search for
```

### Model-Specific Configurations

#### CyberConfig

```python
config = CyberConfig(
    max_pages=20,
    time_window_months=12,
    priority_urls=["/blog", "/news", "/security"],
    keywords=["breach", "incident", "vulnerability"],
    incident_keywords=["breach", "attack", "exploit"],
    hire_keywords=["appointed", "hired", "joins"]
)
```

#### FinancialConfig

```python
config = FinancialConfig(
    max_pages=25,
    document_types=["Annual Report", "Integrated Report"],
    priority_urls=["/investors", "/reports"],
    metric_patterns={
        "Total Assets": r"Total Assets.*?([£$€]\s*[\d,]+\s*(?:billion|million))",
        "Net Income": r"Net Income.*?([£$€]\s*[\d,]+\s*(?:billion|million))"
    }
)
```

#### EnergyConfig

```python
config = EnergyConfig(
    max_pages=15,
    time_window_months=24,
    priority_urls=["/sustainability", "/safety", "/esg"],
    incident_keywords=["spill", "accident", "fatality"]
)
```

## 📊 Results Structure

### CollectionResult

```python
@dataclass
class CollectionResult:
    company_name: str                    # Company analyzed
    website_url: str                     # Website crawled
    collection_date: datetime            # When collected
    signals: List[SignalMatch]           # Signals found
    documents_found: List[str]           # Document URLs
    pages_crawled: int                   # Pages processed
    collection_time: float               # Time taken (seconds)
    success: bool                        # Success flag
    errors: List[str]                    # Any errors
```

### SignalMatch

```python
@dataclass
class SignalMatch:
    keyword: str                         # Matched keyword
    context: str                         # Surrounding context
    url: str                             # Source URL
    date: Optional[datetime]             # Publication date
    source_type: str                     # Type: blog, report, incident, hire
    relevance_score: float               # Relevance (0-1)
```

## 🔧 Advanced Usage

### Custom Keywords

```python
config = CyberConfig(
    keywords=[
        "ransomware", "phishing", "ddos",
        "zero-day", "patch", "vulnerability"
    ],
    incident_keywords=[
        "breach", "attack", "compromise",
        "exploit", "hack", "leak"
    ]
)
```

### Time Window Filtering

```python
# Only analyze last 6 months
config = CyberConfig(time_window_months=6)

# Longer window for safety data
config = EnergyConfig(time_window_months=36)
```

### Priority URL Patterns

```python
config = FinancialConfig(
    priority_urls=[
        "/investors",
        "/investor-relations",
        "/reports",
        "/annual-reports",
        "/financial-information"
    ]
)
```

### Custom Metric Extraction

```python
config = FinancialConfig(
    metric_patterns={
        "Total Assets": r"Total Assets.*?([£$€]\s*[\d,]+\s*(?:billion|million))",
        "Net Income": r"Net Income.*?([£$€]\s*[\d,]+\s*(?:billion|million))",
        "Capital Ratio": r"Capital Ratio.*?([\d.]+%)",
        "NPL Ratio": r"NPL.*?Ratio.*?([\d.]+%)",
        "ROE": r"Return on Equity.*?([\d.]+%)"
    }
)
```

## 🔗 Integration with Pricing

### Complete Workflow

```python
from website_discovery import CorporateWebsiteDiscovery
from signal_collection import CyberSignalCollector, CyberConfig

# Step 1: Discover corporate website
discovery = CorporateWebsiteDiscovery()
discovery_result = discovery.discover("Example Corp")

if not discovery_result.success:
    print("Could not find corporate website")
    exit(1)

website_url = discovery_result.best_match.url

# Step 2: Collect signals
config = CyberConfig()
collector = CyberSignalCollector(config)
collection_result = collector.collect("Example Corp", website_url)

if not collection_result.success:
    print("Could not collect signals")
    exit(1)

# Step 3: Analyze signals for pricing
incidents = [s for s in collection_result.signals
             if s.source_type == "incident"]
hires = [s for s in collection_result.signals
         if s.source_type == "hire"]

# Step 4: Adjust premium
base_premium = 100000

# Increase for recent incidents
if len(incidents) > 0:
    base_premium *= 1.15  # +15% for incidents

# Decrease for new CISO
if len(hires) > 0:
    base_premium *= 0.95  # -5% for key hires

print(f"Adjusted Premium: £{base_premium:,.0f}")
```

### Batch Processing

```python
companies = [
    ("Company A", "https://company-a.com"),
    ("Company B", "https://company-b.com"),
    ("Company C", "https://company-c.com")
]

config = CyberConfig(max_pages=10)
collector = CyberSignalCollector(config)

results = {}
for company_name, website_url in companies:
    result = collector.collect(company_name, website_url)
    results[company_name] = result

    # Rate limiting
    time.sleep(2)

# Analyze results
for company_name, result in results.items():
    if result.success:
        risk_score = calculate_risk_score(result.signals)
        print(f"{company_name}: Risk Score = {risk_score}")
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest models/signal_collection/tests/ -v

# Run specific test
pytest models/signal_collection/tests/test_signal_collection.py::TestCyberSignalCollector -v

# Run with output
pytest models/signal_collection/tests/ -v -s
```

### Test Coverage

- Unit tests for all collectors
- Configuration validation tests
- Integration tests (requires real websites)
- Mock-based tests for offline testing

## 📝 Examples

Run the comprehensive examples:

```bash
cd models/signal_collection
python examples/example_signal_collection.py
```

Examples cover:
1. Cyber security signal collection
2. Financial institution analysis
3. Energy company assessment
4. Custom configurations
5. Batch processing
6. Integration with pricing workflow

## 🏗️ Architecture

```
signal_collection/
├── __init__.py              # Package exports
├── config.py                # Configuration classes
├── crawler.py               # Website crawler
├── collectors.py            # Model-specific collectors
├── extractors/              # Content extractors
│   ├── __init__.py
│   ├── document_extractor.py
│   ├── html_extractor.py
│   └── pdf_extractor.py
├── tests/                   # Test suite
│   ├── __init__.py
│   └── test_signal_collection.py
├── examples/                # Example scripts
│   ├── __init__.py
│   └── example_signal_collection.py
└── README.md               # This file
```

## 🎓 Key Concepts

### Signal

A piece of relevant information extracted from a corporate website (e.g., a security breach mention, a financial metric, a safety incident).

### Collector

A model-specific class that knows what signals to look for and how to extract them.

### Configuration

Defines crawling behavior, keywords, time windows, and other parameters for a specific insurance model.

### Relevance Score

A 0-1 score indicating how relevant a signal is based on context, recency, and other factors.

### Source Type

Classification of where the signal came from:
- `blog`: Blog post or news article
- `report`: PDF report (annual, integrated, etc.)
- `incident`: Identified incident or event
- `hire`: Key personnel hiring announcement
- `web_content`: General website content

## 🔒 Security & Privacy

- Respects robots.txt
- Rate limiting to avoid overwhelming servers
- No authentication bypass
- No scraping of private/member-only content
- User-agent identification
- Polite crawling with delays

## 📈 Performance

### Typical Performance

- **Pages/second**: 0.5-1.0 (with 1-2s delay)
- **Crawl time**: 30-60 seconds for 20-30 pages
- **Memory usage**: ~50-100MB per collection
- **CPU usage**: Low (mostly I/O bound)

### Optimization Tips

1. **Limit pages**: Start with max_pages=10-15
2. **Reduce depth**: max_depth=2 is usually sufficient
3. **Use priority URLs**: Crawl important pages first
4. **Enable caching**: Avoid re-crawling same sites
5. **Batch wisely**: Add delays between companies

## 🐛 Troubleshooting

### No Pages Crawled

- Check website is accessible
- Verify URL format (include https://)
- Check robots.txt isn't blocking
- Increase timeout

### Low Signal Count

- Verify keywords are appropriate
- Check time window isn't too restrictive
- Review priority URLs
- Increase max_pages

### Timeout Errors

- Increase timeout parameter
- Reduce max_pages
- Check network connectivity

### PDF Extraction Fails

- Ensure PyPDF2 and pdfplumber are installed
- Some PDFs may be image-based (no text)
- Try alternative PDF library

## 🚀 Future Enhancements

- [ ] Support for Word/Excel documents
- [ ] Image analysis (logos, screenshots)
- [ ] Natural language processing for sentiment
- [ ] Machine learning for relevance scoring
- [ ] Multi-threaded crawling
- [ ] Distributed collection
- [ ] Cloud storage integration
- [ ] Real-time monitoring

## 📚 Related Modules

- **Website Discovery**: Finds corporate websites from company names
- **Cyber Pricing Model**: Uses cyber signals for premium calculation
- **Financial Institutions Model**: Uses financial signals
- **Energy Model**: Uses energy/safety signals
- **Portfolio Analytics**: Aggregates signals across portfolio

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

## 📄 License

Part of the Digital Signal Intelligence project.

## 📧 Support

For questions or issues, please open an issue in the repository.

---

**Signal Collection Module** - Intelligent extraction of pricing signals from corporate websites.
