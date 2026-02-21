# Phase 2: Continuous Graph Telemetry

## 1. Objective
Transition from "Point-in-Time" API extraction to a continuous "Organisational Graph". Signal extractors must run as asynchronous background workers, allowing the Quoting Engine to return prices in milliseconds by querying a pre-populated graph database.

## 2. Architecture Framework
We will use **Celery** as the distributed task queue and **Redis** as the message broker.

### Step 1: The Worker Implementation (`infrastructure/workers/telemetry.py`)
```python
from celery import Celery
from db.session import get_db
from signal_architecture.extractors import SecurityHeadersExtractor

celery_app = Celery('dsi_telemetry', broker='redis://localhost:6379/0')

@celery_app.task(bind=True, max_retries=3)
def refresh_entity_signal(self, entity_id: str, signal_id: str):
    db = next(get_db())
    try:
        if signal_id == "security_headers":
            extractor = SecurityHeadersExtractor()
            raw_data = extractor.extract(entity_id) # API Call
            
            # Update the RiskSignal table (inferred_value)
            signal_record = db.query(RiskSignal).filter_by(entity_id=entity_id, signal_id=signal_id).first()
            signal_record.inferred_value = raw_data
            db.commit()
            
    except Exception as exc:
        # Log to audit_logs and retry
        self.retry(exc=exc, countdown=60)
```

### Step 2: The Scheduler (Celery Beat)
Configure a scheduler to continuously refresh signals based on their volatility.

* Highly Volatile (e.g., Active CVEs): Refresh every 12 hours.
* Static (e.g., Financial Filings): Refresh every 30 days.

### Step 3: Quoting Engine Refactor
Update /api/v1/quote. It no longer calls extractors. It queries the RiskSignal table.

```python
def generate_quote(entity_id: str, config: CoverageModel):
    # 1. Pull current graph state
    signals = db.query(RiskSignal).filter_by(entity_id=entity_id).all()
    
    # 2. Check signal freshness
    if any(s.last_updated < datetime.now() - timedelta(days=30) for s in signals):
        trigger_synchronous_refresh(entity_id) # Fallback if data is too stale
        
    # 3. Calculate Math
    return run_pricing_engine(signals, config)
```

