"""
DSI Data Persistence Layer
==========================

Handles three core persistence requirements:
1. Signal Cache - Store and reuse extracted signals within TTL
2. Model Registry - Version control for pricing models
3. Quote History - Complete audit trail of all pricing decisions

Architecture:
- Abstract storage interface for flexibility (Redis, PostgreSQL, S3, etc.)
- Time-based signal invalidation with configurable TTL per signal type
- Immutable model versions with semantic versioning
- Complete quote lineage tracking

Author: DSI Framework
Version: 1.0.0
"""

import json
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dsi.persistence")


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class SignalCategory(Enum):
    """Categories of signals with different TTL requirements."""
    STATIC = "static"           # Company registration, founding date - long TTL
    SEMI_STATIC = "semi_static" # Financials, certifications - medium TTL  
    DYNAMIC = "dynamic"         # Security posture, news - short TTL
    REAL_TIME = "real_time"     # Stock price, active incidents - no cache


class ModelStatus(Enum):
    """Lifecycle status of a pricing model version."""
    DRAFT = "draft"             # In development
    TESTING = "testing"         # Under validation
    ACTIVE = "active"           # Production use
    DEPRECATED = "deprecated"   # Phasing out
    RETIRED = "retired"         # No longer available


class QuoteStatus(Enum):
    """Status of a quote through its lifecycle."""
    PENDING = "pending"         # Being processed
    QUOTED = "quoted"           # Quote issued
    REFERRED = "referred"       # Sent for manual review
    DECLINED = "declined"       # Auto-declined
    BOUND = "bound"             # Policy bound
    EXPIRED = "expired"         # Quote validity lapsed
    CANCELLED = "cancelled"     # Cancelled before bind


# Default TTLs by signal category (in seconds)
DEFAULT_TTL = {
    SignalCategory.STATIC: 86400 * 90,      # 90 days
    SignalCategory.SEMI_STATIC: 86400 * 7,  # 7 days
    SignalCategory.DYNAMIC: 3600 * 4,       # 4 hours
    SignalCategory.REAL_TIME: 0,            # No caching
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Signal:
    """Represents an extracted signal with metadata."""
    signal_id: str
    entity_id: str              # Company/risk identifier
    signal_type: str            # e.g., "security_rating", "financial_health"
    signal_name: str            # Human-readable name
    category: SignalCategory
    value: Any                  # The actual signal value
    confidence: float           # 0.0 to 1.0
    source: str                 # Data source
    source_url: Optional[str]
    extracted_at: datetime
    expires_at: datetime
    raw_data: Optional[Dict] = None
    
    def is_valid(self) -> bool:
        """Check if signal is still within TTL."""
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            **asdict(self),
            "category": self.category.value,
            "extracted_at": self.extracted_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Signal":
        """Reconstruct from dictionary."""
        data["category"] = SignalCategory(data["category"])
        if isinstance(data["extracted_at"], str):
            data["extracted_at"] = datetime.fromisoformat(data["extracted_at"])
        if isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        return cls(**data)


@dataclass
class SignalBundle:
    """Collection of signals for an entity at a point in time."""
    bundle_id: str
    entity_id: str
    coverage_type: str
    signals: List[Signal]
    created_at: datetime
    composite_score: Optional[float] = None
    signal_coverage: Optional[float] = None  # % of possible signals found
    
    def get_valid_signals(self) -> List[Signal]:
        """Return only signals still within TTL."""
        return [s for s in self.signals if s.is_valid()]
    
    def get_signal(self, signal_type: str) -> Optional[Signal]:
        """Get a specific signal by type."""
        for s in self.signals:
            if s.signal_type == signal_type and s.is_valid():
                return s
        return None


@dataclass
class ModelVersion:
    """Represents a specific version of a pricing model."""
    model_id: str
    version: str                # Semantic version (e.g., "2.1.0")
    coverage_type: str          # cyber, fi, energy, etc.
    name: str
    description: str
    status: ModelStatus
    created_at: datetime
    created_by: str
    config: Dict                # Model configuration/parameters
    signal_requirements: List[str]  # Required signal types
    thresholds: Dict            # Tier thresholds, limits, etc.
    checksum: str               # Hash of model logic for integrity
    parent_version: Optional[str] = None  # Previous version
    activation_date: Optional[datetime] = None
    retirement_date: Optional[datetime] = None
    performance_metrics: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            **asdict(self),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "activation_date": self.activation_date.isoformat() if self.activation_date else None,
            "retirement_date": self.retirement_date.isoformat() if self.retirement_date else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ModelVersion":
        """Reconstruct from dictionary."""
        data["status"] = ModelStatus(data["status"])
        if isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("activation_date") and isinstance(data["activation_date"], str):
            data["activation_date"] = datetime.fromisoformat(data["activation_date"])
        if data.get("retirement_date") and isinstance(data["retirement_date"], str):
            data["retirement_date"] = datetime.fromisoformat(data["retirement_date"])
        return cls(**data)


@dataclass
class Quote:
    """Complete record of a pricing decision."""
    quote_id: str
    entity_id: str
    entity_name: str
    coverage_type: str
    model_id: str
    model_version: str
    status: QuoteStatus
    created_at: datetime
    expires_at: datetime
    
    # Request details
    requested_limit: float
    requested_currency: str
    effective_date: datetime
    term_months: int
    deductible: Optional[float]
    
    # Assessment results
    composite_score: float
    tier: int
    tier_label: str
    confidence: float
    signal_coverage: float
    
    # Pricing results
    gross_premium: Optional[float]
    net_premium: Optional[float]
    taxes_fees: Optional[float]
    rate_per_million: Optional[float]
    tier_modifier: Optional[float]
    
    # Decision details
    decision_path: str          # straight_through, referred, declined
    decision_reasons: List[str]
    green_flags: List[Dict]
    red_flags: List[Dict]
    amber_flags: List[Dict]
    
    # References
    signal_bundle_id: str       # Link to signals used
    underwriter_id: Optional[str] = None
    policy_id: Optional[str] = None
    parent_quote_id: Optional[str] = None  # For requotes/modifications
    
    # Metadata
    market: str = "us"
    broker_code: Optional[str] = None
    submission_channel: str = "api"
    
    # Direct inquiry responses
    direct_inquiry: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            **asdict(self),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "effective_date": self.effective_date.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Quote":
        """Reconstruct from dictionary."""
        data["status"] = QuoteStatus(data["status"])
        if isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data["expires_at"], str):
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
        if isinstance(data["effective_date"], str):
            data["effective_date"] = datetime.fromisoformat(data["effective_date"])
        return cls(**data)


# =============================================================================
# STORAGE INTERFACE
# =============================================================================

class StorageBackend(ABC):
    """Abstract interface for storage backends."""
    
    @abstractmethod
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
        """Store a value with optional TTL."""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict]:
        """Retrieve a value by key."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value by key."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    def keys(self, pattern: str) -> List[str]:
        """Find keys matching pattern."""
        pass
    
    @abstractmethod
    def mget(self, keys: List[str]) -> List[Optional[Dict]]:
        """Get multiple values."""
        pass
    
    @abstractmethod
    def mset(self, items: Dict[str, Dict], ttl: Optional[int] = None) -> bool:
        """Set multiple values."""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage for development/testing."""
    
    def __init__(self):
        self._store: Dict[str, Tuple[Dict, Optional[datetime]]] = {}
    
    def _is_expired(self, key: str) -> bool:
        if key not in self._store:
            return True
        _, expires = self._store[key]
        if expires and datetime.utcnow() > expires:
            del self._store[key]
            return True
        return False
    
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
        expires = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        self._store[key] = (value, expires)
        return True
    
    def get(self, key: str) -> Optional[Dict]:
        if self._is_expired(key):
            return None
        return self._store.get(key, (None, None))[0]
    
    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        return not self._is_expired(key)
    
    def keys(self, pattern: str) -> List[str]:
        import fnmatch
        # Clean expired keys first
        expired = [k for k in self._store if self._is_expired(k)]
        for k in expired:
            self._store.pop(k, None)
        return [k for k in self._store if fnmatch.fnmatch(k, pattern)]
    
    def mget(self, keys: List[str]) -> List[Optional[Dict]]:
        return [self.get(k) for k in keys]
    
    def mset(self, items: Dict[str, Dict], ttl: Optional[int] = None) -> bool:
        for k, v in items.items():
            self.set(k, v, ttl)
        return True


# =============================================================================
# SIGNAL CACHE
# =============================================================================

class SignalCache:
    """
    Manages signal extraction caching with TTL-based invalidation.
    
    Key schema: signal:{entity_id}:{signal_type}
    Bundle schema: bundle:{bundle_id}
    """
    
    def __init__(self, storage: StorageBackend, custom_ttl: Optional[Dict[str, int]] = None):
        self.storage = storage
        self.ttl_config = {**DEFAULT_TTL}
        if custom_ttl:
            for k, v in custom_ttl.items():
                if isinstance(k, str):
                    k = SignalCategory(k)
                self.ttl_config[k] = v
    
    def _signal_key(self, entity_id: str, signal_type: str) -> str:
        return f"signal:{entity_id}:{signal_type}"
    
    def _bundle_key(self, bundle_id: str) -> str:
        return f"bundle:{bundle_id}"
    
    def _entity_index_key(self, entity_id: str) -> str:
        return f"entity_signals:{entity_id}"
    
    def get_ttl(self, category: SignalCategory) -> int:
        """Get TTL in seconds for a signal category."""
        return self.ttl_config.get(category, DEFAULT_TTL[category])
    
    def store_signal(self, signal: Signal) -> bool:
        """Store a single signal with appropriate TTL."""
        key = self._signal_key(signal.entity_id, signal.signal_type)
        ttl = self.get_ttl(signal.category)
        
        if ttl == 0:  # Real-time signals are not cached
            logger.debug(f"Skipping cache for real-time signal: {signal.signal_type}")
            return False
        
        success = self.storage.set(key, signal.to_dict(), ttl)
        
        # Update entity index
        if success:
            index_key = self._entity_index_key(signal.entity_id)
            index = self.storage.get(index_key) or {"signals": []}
            if signal.signal_type not in index["signals"]:
                index["signals"].append(signal.signal_type)
                self.storage.set(index_key, index, ttl=86400 * 365)  # 1 year index
        
        logger.info(f"Cached signal {signal.signal_type} for {signal.entity_id} (TTL: {ttl}s)")
        return success
    
    def get_signal(self, entity_id: str, signal_type: str) -> Optional[Signal]:
        """Retrieve a cached signal if valid."""
        key = self._signal_key(entity_id, signal_type)
        data = self.storage.get(key)
        
        if data:
            signal = Signal.from_dict(data)
            if signal.is_valid():
                logger.debug(f"Cache HIT: {signal_type} for {entity_id}")
                return signal
            else:
                logger.debug(f"Cache EXPIRED: {signal_type} for {entity_id}")
                self.storage.delete(key)
        else:
            logger.debug(f"Cache MISS: {signal_type} for {entity_id}")
        
        return None
    
    def get_signals(self, entity_id: str, signal_types: List[str]) -> Dict[str, Optional[Signal]]:
        """Retrieve multiple signals for an entity."""
        keys = [self._signal_key(entity_id, st) for st in signal_types]
        results = self.storage.mget(keys)
        
        output = {}
        for signal_type, data in zip(signal_types, results):
            if data:
                signal = Signal.from_dict(data)
                output[signal_type] = signal if signal.is_valid() else None
            else:
                output[signal_type] = None
        
        hits = sum(1 for v in output.values() if v is not None)
        logger.info(f"Bulk cache lookup for {entity_id}: {hits}/{len(signal_types)} hits")
        return output
    
    def store_bundle(self, bundle: SignalBundle) -> bool:
        """Store a complete signal bundle and its individual signals."""
        # Store individual signals
        for signal in bundle.signals:
            self.store_signal(signal)
        
        # Store bundle reference
        bundle_data = {
            "bundle_id": bundle.bundle_id,
            "entity_id": bundle.entity_id,
            "coverage_type": bundle.coverage_type,
            "signal_types": [s.signal_type for s in bundle.signals],
            "created_at": bundle.created_at.isoformat(),
            "composite_score": bundle.composite_score,
            "signal_coverage": bundle.signal_coverage,
        }
        
        key = self._bundle_key(bundle.bundle_id)
        return self.storage.set(key, bundle_data, ttl=86400 * 30)  # 30 day bundle reference
    
    def get_bundle(self, bundle_id: str) -> Optional[SignalBundle]:
        """Retrieve a bundle by ID, refreshing from individual signals."""
        key = self._bundle_key(bundle_id)
        data = self.storage.get(key)
        
        if not data:
            return None
        
        # Reconstruct bundle with current signal states
        signal_cache = self.get_signals(data["entity_id"], data["signal_types"])
        valid_signals = [s for s in signal_cache.values() if s is not None]
        
        return SignalBundle(
            bundle_id=data["bundle_id"],
            entity_id=data["entity_id"],
            coverage_type=data["coverage_type"],
            signals=valid_signals,
            created_at=datetime.fromisoformat(data["created_at"]),
            composite_score=data.get("composite_score"),
            signal_coverage=data.get("signal_coverage"),
        )
    
    def invalidate_entity(self, entity_id: str) -> int:
        """Invalidate all cached signals for an entity."""
        index_key = self._entity_index_key(entity_id)
        index = self.storage.get(index_key)
        
        if not index:
            return 0
        
        count = 0
        for signal_type in index.get("signals", []):
            key = self._signal_key(entity_id, signal_type)
            if self.storage.delete(key):
                count += 1
        
        self.storage.delete(index_key)
        logger.info(f"Invalidated {count} signals for entity {entity_id}")
        return count
    
    def get_cache_stats(self, entity_id: str) -> Dict:
        """Get cache statistics for an entity."""
        index_key = self._entity_index_key(entity_id)
        index = self.storage.get(index_key)
        
        if not index:
            return {"entity_id": entity_id, "cached_signals": 0, "valid_signals": 0}
        
        signal_types = index.get("signals", [])
        signals = self.get_signals(entity_id, signal_types)
        
        valid = sum(1 for s in signals.values() if s is not None)
        
        return {
            "entity_id": entity_id,
            "cached_signals": len(signal_types),
            "valid_signals": valid,
            "signal_types": signal_types,
            "hit_rate": valid / len(signal_types) if signal_types else 0,
        }


# =============================================================================
# MODEL REGISTRY
# =============================================================================

class ModelRegistry:
    """
    Version-controlled registry for pricing models.
    
    Key schema: model:{coverage_type}:{version}
    Active schema: model_active:{coverage_type}
    """
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
    
    def _model_key(self, coverage_type: str, version: str) -> str:
        return f"model:{coverage_type}:{version}"
    
    def _active_key(self, coverage_type: str) -> str:
        return f"model_active:{coverage_type}"
    
    def _history_key(self, coverage_type: str) -> str:
        return f"model_history:{coverage_type}"
    
    def _compute_checksum(self, config: Dict) -> str:
        """Compute checksum of model configuration."""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def register_model(self, model: ModelVersion) -> bool:
        """Register a new model version."""
        key = self._model_key(model.coverage_type, model.version)
        
        # Check if version already exists
        if self.storage.exists(key):
            logger.error(f"Model version {model.version} already exists for {model.coverage_type}")
            return False
        
        # Store model
        success = self.storage.set(key, model.to_dict())
        
        if success:
            # Update history
            history_key = self._history_key(model.coverage_type)
            history = self.storage.get(history_key) or {"versions": []}
            history["versions"].append({
                "version": model.version,
                "status": model.status.value,
                "created_at": model.created_at.isoformat(),
            })
            self.storage.set(history_key, history)
            
            logger.info(f"Registered model {model.coverage_type} v{model.version}")
        
        return success
    
    def get_model(self, coverage_type: str, version: str) -> Optional[ModelVersion]:
        """Retrieve a specific model version."""
        key = self._model_key(coverage_type, version)
        data = self.storage.get(key)
        return ModelVersion.from_dict(data) if data else None
    
    def get_active_model(self, coverage_type: str) -> Optional[ModelVersion]:
        """Get the currently active model for a coverage type."""
        active_key = self._active_key(coverage_type)
        active = self.storage.get(active_key)
        
        if not active:
            return None
        
        return self.get_model(coverage_type, active["version"])
    
    def activate_model(self, coverage_type: str, version: str) -> bool:
        """Set a model version as the active production version."""
        model = self.get_model(coverage_type, version)
        
        if not model:
            logger.error(f"Model {coverage_type} v{version} not found")
            return False
        
        if model.status not in [ModelStatus.TESTING, ModelStatus.ACTIVE]:
            logger.error(f"Cannot activate model in {model.status.value} status")
            return False
        
        # Deactivate current active model
        current = self.get_active_model(coverage_type)
        if current and current.version != version:
            current.status = ModelStatus.DEPRECATED
            current.retirement_date = datetime.utcnow()
            self.storage.set(
                self._model_key(coverage_type, current.version),
                current.to_dict()
            )
        
        # Activate new model
        model.status = ModelStatus.ACTIVE
        model.activation_date = datetime.utcnow()
        self.storage.set(self._model_key(coverage_type, version), model.to_dict())
        
        # Update active pointer
        self.storage.set(self._active_key(coverage_type), {
            "version": version,
            "activated_at": datetime.utcnow().isoformat(),
        })
        
        logger.info(f"Activated model {coverage_type} v{version}")
        return True
    
    def get_model_history(self, coverage_type: str) -> List[Dict]:
        """Get version history for a coverage type."""
        history_key = self._history_key(coverage_type)
        history = self.storage.get(history_key)
        return history.get("versions", []) if history else []
    
    def list_models(self, coverage_type: Optional[str] = None, 
                    status: Optional[ModelStatus] = None) -> List[ModelVersion]:
        """List models with optional filters."""
        if coverage_type:
            pattern = f"model:{coverage_type}:*"
        else:
            pattern = "model:*:*"
        
        keys = self.storage.keys(pattern)
        # Filter out non-version keys
        keys = [k for k in keys if k.count(":") == 2]
        
        models = []
        for key in keys:
            data = self.storage.get(key)
            if data:
                model = ModelVersion.from_dict(data)
                if status is None or model.status == status:
                    models.append(model)
        
        return sorted(models, key=lambda m: (m.coverage_type, m.version))
    
    def create_variant(self, base_version: ModelVersion, 
                       new_version: str,
                       config_overrides: Dict,
                       description: str) -> ModelVersion:
        """Create a new model variant from an existing version."""
        new_config = {**base_version.config, **config_overrides}
        
        variant = ModelVersion(
            model_id=str(uuid.uuid4()),
            version=new_version,
            coverage_type=base_version.coverage_type,
            name=f"{base_version.name} (variant)",
            description=description,
            status=ModelStatus.DRAFT,
            created_at=datetime.utcnow(),
            created_by="system",
            config=new_config,
            signal_requirements=base_version.signal_requirements,
            thresholds=base_version.thresholds,
            checksum=self._compute_checksum(new_config),
            parent_version=base_version.version,
        )
        
        self.register_model(variant)
        return variant


# =============================================================================
# QUOTE REPOSITORY
# =============================================================================

class QuoteRepository:
    """
    Repository for quote storage and retrieval.
    
    Key schema: quote:{quote_id}
    Entity index: quotes_by_entity:{entity_id}
    Time index: quotes_by_date:{YYYY-MM-DD}
    """
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
    
    def _quote_key(self, quote_id: str) -> str:
        return f"quote:{quote_id}"
    
    def _entity_index_key(self, entity_id: str) -> str:
        return f"quotes_by_entity:{entity_id}"
    
    def _date_index_key(self, date: datetime) -> str:
        return f"quotes_by_date:{date.strftime('%Y-%m-%d')}"
    
    def _model_index_key(self, model_id: str, version: str) -> str:
        return f"quotes_by_model:{model_id}:{version}"
    
    def save(self, quote: Quote) -> bool:
        """Save a quote and update all indexes."""
        key = self._quote_key(quote.quote_id)
        success = self.storage.set(key, quote.to_dict())
        
        if success:
            # Update entity index
            entity_idx = self._entity_index_key(quote.entity_id)
            entity_quotes = self.storage.get(entity_idx) or {"quote_ids": []}
            if quote.quote_id not in entity_quotes["quote_ids"]:
                entity_quotes["quote_ids"].append(quote.quote_id)
                self.storage.set(entity_idx, entity_quotes)
            
            # Update date index
            date_idx = self._date_index_key(quote.created_at)
            date_quotes = self.storage.get(date_idx) or {"quote_ids": []}
            if quote.quote_id not in date_quotes["quote_ids"]:
                date_quotes["quote_ids"].append(quote.quote_id)
                self.storage.set(date_idx, date_quotes)
            
            # Update model index
            model_idx = self._model_index_key(quote.model_id, quote.model_version)
            model_quotes = self.storage.get(model_idx) or {"quote_ids": []}
            if quote.quote_id not in model_quotes["quote_ids"]:
                model_quotes["quote_ids"].append(quote.quote_id)
                self.storage.set(model_idx, model_quotes)
            
            logger.info(f"Saved quote {quote.quote_id} for {quote.entity_name}")
        
        return success
    
    def get(self, quote_id: str) -> Optional[Quote]:
        """Retrieve a quote by ID."""
        key = self._quote_key(quote_id)
        data = self.storage.get(key)
        return Quote.from_dict(data) if data else None
    
    def get_by_entity(self, entity_id: str, 
                      limit: int = 100,
                      status: Optional[QuoteStatus] = None) -> List[Quote]:
        """Get all quotes for an entity."""
        entity_idx = self._entity_index_key(entity_id)
        index = self.storage.get(entity_idx)
        
        if not index:
            return []
        
        quote_ids = index.get("quote_ids", [])[-limit:]
        quotes = []
        
        for qid in quote_ids:
            quote = self.get(qid)
            if quote and (status is None or quote.status == status):
                quotes.append(quote)
        
        return sorted(quotes, key=lambda q: q.created_at, reverse=True)
    
    def get_by_date_range(self, start: datetime, end: datetime,
                          coverage_type: Optional[str] = None) -> List[Quote]:
        """Get quotes within a date range."""
        quotes = []
        current = start
        
        while current <= end:
            date_idx = self._date_index_key(current)
            index = self.storage.get(date_idx)
            
            if index:
                for qid in index.get("quote_ids", []):
                    quote = self.get(qid)
                    if quote:
                        if coverage_type is None or quote.coverage_type == coverage_type:
                            quotes.append(quote)
            
            current += timedelta(days=1)
        
        return sorted(quotes, key=lambda q: q.created_at)
    
    def update_status(self, quote_id: str, status: QuoteStatus, 
                      underwriter_id: Optional[str] = None,
                      policy_id: Optional[str] = None) -> bool:
        """Update quote status (e.g., when bound or expired)."""
        quote = self.get(quote_id)
        if not quote:
            return False
        
        quote.status = status
        if underwriter_id:
            quote.underwriter_id = underwriter_id
        if policy_id:
            quote.policy_id = policy_id
        
        return self.save(quote)
    
    def get_quote_lineage(self, quote_id: str) -> List[Quote]:
        """Get the full lineage of a quote (parent chain)."""
        lineage = []
        current = self.get(quote_id)
        
        while current:
            lineage.append(current)
            if current.parent_quote_id:
                current = self.get(current.parent_quote_id)
            else:
                break
        
        return lineage
    
    def get_analytics(self, coverage_type: Optional[str] = None,
                      days: int = 30) -> Dict:
        """Get quote analytics for the specified period."""
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        
        quotes = self.get_by_date_range(start, end, coverage_type)
        
        if not quotes:
            return {"period_days": days, "total_quotes": 0}
        
        stats = {
            "period_days": days,
            "total_quotes": len(quotes),
            "by_status": {},
            "by_decision_path": {},
            "avg_score": 0,
            "avg_premium": 0,
            "bind_rate": 0,
            "straight_through_rate": 0,
        }
        
        scores = []
        premiums = []
        
        for q in quotes:
            # Status counts
            status = q.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Decision path counts
            path = q.decision_path
            stats["by_decision_path"][path] = stats["by_decision_path"].get(path, 0) + 1
            
            scores.append(q.composite_score)
            if q.gross_premium:
                premiums.append(q.gross_premium)
        
        stats["avg_score"] = sum(scores) / len(scores) if scores else 0
        stats["avg_premium"] = sum(premiums) / len(premiums) if premiums else 0
        
        bound = stats["by_status"].get("bound", 0)
        stats["bind_rate"] = bound / len(quotes) if quotes else 0
        
        stp = stats["by_decision_path"].get("straight_through", 0)
        stats["straight_through_rate"] = stp / len(quotes) if quotes else 0
        
        return stats


# =============================================================================
# UNIFIED DSI PERSISTENCE SERVICE
# =============================================================================

class DSIPersistenceService:
    """
    Unified service coordinating all persistence operations.
    
    This is the main entry point for the DSI workflow.
    """
    
    def __init__(self, storage: Optional[StorageBackend] = None,
                 signal_ttl_overrides: Optional[Dict] = None):
        self.storage = storage or InMemoryStorage()
        self.signal_cache = SignalCache(self.storage, signal_ttl_overrides)
        self.model_registry = ModelRegistry(self.storage)
        self.quote_repo = QuoteRepository(self.storage)
    
    def process_signals(self, entity_id: str, 
                        required_signals: List[str],
                        extract_func) -> Tuple[SignalBundle, Dict]:
        """
        Process signals with cache-aware extraction.
        
        Returns tuple of (bundle, cache_stats) where cache_stats shows
        what was cached vs freshly extracted.
        """
        # Check cache first
        cached = self.signal_cache.get_signals(entity_id, required_signals)
        
        # Identify what needs extraction
        to_extract = [st for st, sig in cached.items() if sig is None]
        
        cache_stats = {
            "total_required": len(required_signals),
            "cache_hits": len(required_signals) - len(to_extract),
            "cache_misses": len(to_extract),
            "hit_rate": (len(required_signals) - len(to_extract)) / len(required_signals),
        }
        
        # Extract missing signals
        if to_extract:
            new_signals = extract_func(entity_id, to_extract)
            for signal in new_signals:
                self.signal_cache.store_signal(signal)
                cached[signal.signal_type] = signal
        
        # Build bundle
        all_signals = [s for s in cached.values() if s is not None]
        bundle = SignalBundle(
            bundle_id=str(uuid.uuid4()),
            entity_id=entity_id,
            coverage_type="",  # Set by caller
            signals=all_signals,
            created_at=datetime.utcnow(),
            signal_coverage=len(all_signals) / len(required_signals),
        )
        
        return bundle, cache_stats
    
    def run_pricing(self, entity_id: str,
                    entity_name: str,
                    coverage_type: str,
                    limit: float,
                    currency: str,
                    effective_date: datetime,
                    term_months: int,
                    deductible: Optional[float],
                    direct_inquiry: Dict[str, bool],
                    market: str,
                    extract_func,
                    price_func) -> Quote:
        """
        Execute complete pricing workflow with persistence.
        
        This is the main entry point for pricing requests.
        """
        # Get active model
        model = self.model_registry.get_active_model(coverage_type)
        if not model:
            raise ValueError(f"No active model for coverage type: {coverage_type}")
        
        # Process signals
        bundle, cache_stats = self.process_signals(
            entity_id, 
            model.signal_requirements,
            extract_func
        )
        bundle.coverage_type = coverage_type
        
        # Store bundle
        self.signal_cache.store_bundle(bundle)
        
        # Run pricing model
        pricing_result = price_func(
            signals=bundle.signals,
            limit=limit,
            deductible=deductible,
            model_config=model.config,
            thresholds=model.thresholds,
        )
        
        # Determine decision path
        if pricing_result["tier"] <= 2 and not pricing_result.get("red_flags"):
            decision_path = "straight_through"
            status = QuoteStatus.QUOTED
        elif pricing_result["tier"] == 5 or pricing_result.get("critical_flags"):
            decision_path = "declined"
            status = QuoteStatus.DECLINED
        else:
            decision_path = "referred"
            status = QuoteStatus.REFERRED
        
        # Create quote
        quote = Quote(
            quote_id=str(uuid.uuid4()),
            entity_id=entity_id,
            entity_name=entity_name,
            coverage_type=coverage_type,
            model_id=model.model_id,
            model_version=model.version,
            status=status,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            requested_limit=limit,
            requested_currency=currency,
            effective_date=effective_date,
            term_months=term_months,
            deductible=deductible,
            composite_score=pricing_result["composite_score"],
            tier=pricing_result["tier"],
            tier_label=pricing_result["tier_label"],
            confidence=pricing_result.get("confidence", 0.0),
            signal_coverage=bundle.signal_coverage,
            gross_premium=pricing_result.get("gross_premium"),
            net_premium=pricing_result.get("net_premium"),
            taxes_fees=pricing_result.get("taxes_fees"),
            rate_per_million=pricing_result.get("rate_per_million"),
            tier_modifier=pricing_result.get("tier_modifier"),
            decision_path=decision_path,
            decision_reasons=pricing_result.get("decision_reasons", []),
            green_flags=pricing_result.get("green_flags", []),
            red_flags=pricing_result.get("red_flags", []),
            amber_flags=pricing_result.get("amber_flags", []),
            signal_bundle_id=bundle.bundle_id,
            market=market,
            direct_inquiry=direct_inquiry,
        )
        
        # Save quote
        self.quote_repo.save(quote)
        
        logger.info(
            f"Pricing complete: {entity_name} | "
            f"Score: {quote.composite_score} | "
            f"Tier: {quote.tier_label} | "
            f"Path: {decision_path} | "
            f"Cache: {cache_stats['hit_rate']:.0%}"
        )
        
        return quote
    
    def requote(self, original_quote_id: str,
                limit: Optional[float] = None,
                deductible: Optional[float] = None,
                effective_date: Optional[datetime] = None,
                extract_func=None,
                price_func=None) -> Quote:
        """
        Create a new quote based on an existing one with modifications.
        """
        original = self.quote_repo.get(original_quote_id)
        if not original:
            raise ValueError(f"Quote not found: {original_quote_id}")
        
        # Run new pricing with modified parameters
        new_quote = self.run_pricing(
            entity_id=original.entity_id,
            entity_name=original.entity_name,
            coverage_type=original.coverage_type,
            limit=limit or original.requested_limit,
            currency=original.requested_currency,
            effective_date=effective_date or original.effective_date,
            term_months=original.term_months,
            deductible=deductible if deductible is not None else original.deductible,
            direct_inquiry=original.direct_inquiry or {},
            market=original.market,
            extract_func=extract_func,
            price_func=price_func,
        )
        
        # Link to original
        new_quote.parent_quote_id = original_quote_id
        self.quote_repo.save(new_quote)
        
        return new_quote
    
    def get_entity_profile(self, entity_id: str) -> Dict:
        """Get comprehensive profile for an entity."""
        cache_stats = self.signal_cache.get_cache_stats(entity_id)
        quotes = self.quote_repo.get_by_entity(entity_id, limit=50)
        
        return {
            "entity_id": entity_id,
            "signal_cache": cache_stats,
            "quote_count": len(quotes),
            "latest_quote": quotes[0].to_dict() if quotes else None,
            "quote_history": [
                {
                    "quote_id": q.quote_id,
                    "coverage_type": q.coverage_type,
                    "status": q.status.value,
                    "score": q.composite_score,
                    "created_at": q.created_at.isoformat(),
                }
                for q in quotes[:10]
            ],
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Initialize service
    service = DSIPersistenceService()
    
    # Example: Register a model
    cyber_model = ModelVersion(
        model_id=str(uuid.uuid4()),
        version="2.0.0",
        coverage_type="cyber",
        name="DSI Cyber Pricing Model",
        description="Production cyber liability pricing with network signals",
        status=ModelStatus.TESTING,
        created_at=datetime.utcnow(),
        created_by="dsi_admin",
        config={
            "base_rate": 2500,
            "min_premium": 5000,
            "max_tier_modifier": 3.0,
        },
        signal_requirements=[
            "security_rating",
            "vulnerability_count",
            "breach_history",
            "compliance_status",
            "technology_stack",
        ],
        thresholds={
            "tier_1": 800,
            "tier_2": 650,
            "tier_3": 500,
            "tier_4": 350,
        },
        checksum="abc123",
    )
    
    service.model_registry.register_model(cyber_model)
    service.model_registry.activate_model("cyber", "2.0.0")
    
    # Example: Cache some signals
    test_signal = Signal(
        signal_id=str(uuid.uuid4()),
        entity_id="acme-corp-123",
        signal_type="security_rating",
        signal_name="Security Scorecard Rating",
        category=SignalCategory.DYNAMIC,
        value={"score": 85, "grade": "A"},
        confidence=0.92,
        source="SecurityScorecard",
        source_url="https://securityscorecard.com/...",
        extracted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=4),
    )
    
    service.signal_cache.store_signal(test_signal)
    
    # Retrieve
    cached = service.signal_cache.get_signal("acme-corp-123", "security_rating")
    print(f"Cached signal: {cached.value if cached else 'Not found'}")
    
    # Check stats
    stats = service.signal_cache.get_cache_stats("acme-corp-123")
    print(f"Cache stats: {stats}")
    
    print("\nDSI Persistence Layer initialized successfully!")
