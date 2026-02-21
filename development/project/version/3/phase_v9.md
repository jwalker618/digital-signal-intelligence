# Phase 9: Engineering the Deterministic Referral Backend

## Objective
To physically implement the database models, Pydantic schemas, and API endpoints required to support the Phase 8 "Signal Auditing" methodology. The system must immutable track human overrides without destroying original machine inferences.

## 1. Database Model Updates (SQLAlchemy)
Update `db/models.py` to support dual-state signals and JSONB audit trails.

```python
# Refactoring the Signal model
class RiskSignal(Base):
    __tablename__ = "risk_signals"
    id = Column(UUID(as_uuid=True), primary_key=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"))
    signal_id = Column(String(100), nullable=False)
    
    # The immutable machine truth
    inferred_value = Column(JSONB, nullable=True) 
    
    # The mutable human truth (Defaults to inferred_value)
    audited_value = Column(JSONB, nullable=True)  
    
    is_overridden = Column(Boolean, default=False)
    
    # The Phase 8 requirements
    audit_trail = Column(JSONB, nullable=True) # {user_id, timestamp, rationale, evidence}

```


## 2. API Endpoint (api/endpoints/submissions.py)
Create the /override endpoint that accepts a factual correction, updates the audited_value, and automatically triggers a new Model Cycle via the pricing engine, returning Version N+1 of the quote.

## 3. Scorer Engine Refactor
Update layers/risk/scorer.py to strictly query signal.audited_value for all mathematical calculations, completely ignoring inferred_value during the math phase.
