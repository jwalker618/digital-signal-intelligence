"""
PostgreSQL Storage Backend for DSI Persistence
==============================================

Production-ready PostgreSQL implementation for:
- Durable quote storage
- Model version control
- Audit trail
- Complex queries and analytics

Schema designed for:
- Write-ahead logging for durability
- JSONB for flexible signal storage
- Indexes for common query patterns
- Partitioning for time-series data

Requirements:
    pip install psycopg2-binary

Author: John Walker
Version: 1.0.0
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    from psycopg2.pool import ThreadedConnectionPool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from dsi_persistence import StorageBackend

logger = logging.getLogger("dsi.persistence.postgres")


# SQL Schema
SCHEMA_SQL = """
-- Signal cache table
CREATE TABLE IF NOT EXISTS dsi_signals (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(64) UNIQUE NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    signal_type VARCHAR(64) NOT NULL,
    signal_name VARCHAR(256),
    category VARCHAR(32) NOT NULL,
    value JSONB NOT NULL,
    confidence FLOAT,
    source VARCHAR(128),
    source_url TEXT,
    raw_data JSONB,
    extracted_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(entity_id, signal_type)
);

CREATE INDEX IF NOT EXISTS idx_signals_entity ON dsi_signals(entity_id);
CREATE INDEX IF NOT EXISTS idx_signals_expires ON dsi_signals(expires_at);
CREATE INDEX IF NOT EXISTS idx_signals_type ON dsi_signals(signal_type);

-- Signal bundles table
CREATE TABLE IF NOT EXISTS dsi_signal_bundles (
    id SERIAL PRIMARY KEY,
    bundle_id VARCHAR(64) UNIQUE NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    coverage_type VARCHAR(32) NOT NULL,
    signal_types JSONB NOT NULL,
    composite_score FLOAT,
    signal_coverage FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bundles_entity ON dsi_signal_bundles(entity_id);

-- Model versions table
CREATE TABLE IF NOT EXISTS dsi_models (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(64) UNIQUE NOT NULL,
    version VARCHAR(32) NOT NULL,
    coverage_type VARCHAR(32) NOT NULL,
    name VARCHAR(256) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL,
    config JSONB NOT NULL,
    signal_requirements JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    checksum VARCHAR(64),
    parent_version VARCHAR(32),
    performance_metrics JSONB,
    created_by VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW(),
    activation_date TIMESTAMP,
    retirement_date TIMESTAMP,
    
    UNIQUE(coverage_type, version)
);

CREATE INDEX IF NOT EXISTS idx_models_coverage ON dsi_models(coverage_type);
CREATE INDEX IF NOT EXISTS idx_models_status ON dsi_models(status);

-- Active model pointers
CREATE TABLE IF NOT EXISTS dsi_active_models (
    coverage_type VARCHAR(32) PRIMARY KEY,
    model_id VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL,
    activated_at TIMESTAMP DEFAULT NOW()
);

-- Quotes table (main transaction table)
CREATE TABLE IF NOT EXISTS dsi_quotes (
    id SERIAL PRIMARY KEY,
    quote_id VARCHAR(64) UNIQUE NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    entity_name VARCHAR(256) NOT NULL,
    coverage_type VARCHAR(32) NOT NULL,
    model_id VARCHAR(64) NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    
    -- Request details
    requested_limit DECIMAL(18, 2) NOT NULL,
    requested_currency VARCHAR(3) NOT NULL,
    effective_date DATE NOT NULL,
    term_months INT NOT NULL,
    deductible DECIMAL(18, 2),
    
    -- Assessment results
    composite_score FLOAT NOT NULL,
    tier INT NOT NULL,
    tier_label VARCHAR(32) NOT NULL,
    confidence FLOAT,
    signal_coverage FLOAT,
    
    -- Pricing results
    gross_premium DECIMAL(18, 2),
    net_premium DECIMAL(18, 2),
    taxes_fees DECIMAL(18, 2),
    rate_per_million DECIMAL(12, 4),
    tier_modifier DECIMAL(8, 4),
    
    -- Decision details
    decision_path VARCHAR(32) NOT NULL,
    decision_reasons JSONB,
    green_flags JSONB,
    red_flags JSONB,
    amber_flags JSONB,
    
    -- References
    signal_bundle_id VARCHAR(64),
    underwriter_id VARCHAR(64),
    policy_id VARCHAR(64),
    parent_quote_id VARCHAR(64),
    
    -- Metadata
    market VARCHAR(32) DEFAULT 'us',
    broker_code VARCHAR(64),
    submission_channel VARCHAR(32) DEFAULT 'api',
    direct_inquiry JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quotes_entity ON dsi_quotes(entity_id);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON dsi_quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_coverage ON dsi_quotes(coverage_type);
CREATE INDEX IF NOT EXISTS idx_quotes_created ON dsi_quotes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quotes_model ON dsi_quotes(model_id, model_version);

-- Quote audit log
CREATE TABLE IF NOT EXISTS dsi_quote_audit (
    id SERIAL PRIMARY KEY,
    quote_id VARCHAR(64) NOT NULL,
    action VARCHAR(32) NOT NULL,
    old_status VARCHAR(32),
    new_status VARCHAR(32),
    changed_by VARCHAR(128),
    change_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_quote ON dsi_quote_audit(quote_id);

-- Key-value store for generic storage interface compatibility
CREATE TABLE IF NOT EXISTS dsi_kv_store (
    key VARCHAR(512) PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kv_expires ON dsi_kv_store(expires_at);
"""


class PostgresStorage(StorageBackend):
    """
    PostgreSQL-backed storage for durable persistence.
    
    Provides both:
    1. Key-value interface (for StorageBackend compatibility)
    2. Relational methods for complex queries
    """
    
    def __init__(self,
                 host: str = "localhost",
                 port: int = 5432,
                 database: str = "dsi",
                 user: str = "dsi_user",
                 password: str = "",
                 min_connections: int = 5,
                 max_connections: int = 20,
                 auto_create_schema: bool = True):
        """
        Initialize PostgreSQL connection pool.
        """
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 package required: pip install psycopg2-binary")
        
        self.pool = ThreadedConnectionPool(
            minconn=min_connections,
            maxconn=max_connections,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        
        if auto_create_schema:
            self._create_schema()
        
        logger.info(f"Connected to PostgreSQL at {host}:{port}/{database}")
    
    def _create_schema(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
        logger.info("Database schema initialized")
    
    @contextmanager
    def _get_connection(self):
        """Get connection from pool with automatic return."""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    # ==========================================================================
    # StorageBackend interface (key-value)
    # ==========================================================================
    
    def set(self, key: str, value: Dict, ttl: Optional[int] = None) -> bool:
        """Store a value in key-value table."""
        try:
            expires = None
            if ttl:
                from datetime import timedelta
                expires = datetime.utcnow() + timedelta(seconds=ttl)
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dsi_kv_store (key, value, expires_at, updated_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (key) DO UPDATE SET
                            value = EXCLUDED.value,
                            expires_at = EXCLUDED.expires_at,
                            updated_at = NOW()
                    """, (key, Json(value), expires))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL SET error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Dict]:
        """Retrieve a value from key-value table."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT value FROM dsi_kv_store
                        WHERE key = %s
                        AND (expires_at IS NULL OR expires_at > NOW())
                    """, (key,))
                    row = cur.fetchone()
                    return row["value"] if row else None
        except Exception as e:
            logger.error(f"PostgreSQL GET error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a value from key-value table."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM dsi_kv_store WHERE key = %s", (key,))
                    deleted = cur.rowcount > 0
                conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"PostgreSQL DELETE error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in key-value table."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 1 FROM dsi_kv_store
                        WHERE key = %s
                        AND (expires_at IS NULL OR expires_at > NOW())
                    """, (key,))
                    return cur.fetchone() is not None
        except Exception as e:
            logger.error(f"PostgreSQL EXISTS error: {e}")
            return False
    
    def keys(self, pattern: str) -> List[str]:
        """Find keys matching pattern (SQL LIKE pattern)."""
        try:
            # Convert glob pattern to SQL LIKE pattern
            sql_pattern = pattern.replace("*", "%").replace("?", "_")
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT key FROM dsi_kv_store
                        WHERE key LIKE %s
                        AND (expires_at IS NULL OR expires_at > NOW())
                    """, (sql_pattern,))
                    return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"PostgreSQL KEYS error: {e}")
            return []
    
    def mget(self, keys: List[str]) -> List[Optional[Dict]]:
        """Get multiple values."""
        if not keys:
            return []
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT key, value FROM dsi_kv_store
                        WHERE key = ANY(%s)
                        AND (expires_at IS NULL OR expires_at > NOW())
                    """, (keys,))
                    
                    results = {row["key"]: row["value"] for row in cur.fetchall()}
                    return [results.get(k) for k in keys]
        except Exception as e:
            logger.error(f"PostgreSQL MGET error: {e}")
            return [None] * len(keys)
    
    def mset(self, items: Dict[str, Dict], ttl: Optional[int] = None) -> bool:
        """Set multiple values."""
        if not items:
            return True
        
        try:
            expires = None
            if ttl:
                from datetime import timedelta
                expires = datetime.utcnow() + timedelta(seconds=ttl)
            
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    for key, value in items.items():
                        cur.execute("""
                            INSERT INTO dsi_kv_store (key, value, expires_at, updated_at)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (key) DO UPDATE SET
                                value = EXCLUDED.value,
                                expires_at = EXCLUDED.expires_at,
                                updated_at = NOW()
                        """, (key, Json(value), expires))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL MSET error: {e}")
            return False
    
    # ==========================================================================
    # Relational methods for quotes
    # ==========================================================================
    
    def save_quote(self, quote_data: Dict) -> bool:
        """Save a quote with full relational storage."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dsi_quotes (
                            quote_id, entity_id, entity_name, coverage_type,
                            model_id, model_version, status,
                            requested_limit, requested_currency, effective_date,
                            term_months, deductible,
                            composite_score, tier, tier_label, confidence, signal_coverage,
                            gross_premium, net_premium, taxes_fees, rate_per_million, tier_modifier,
                            decision_path, decision_reasons, green_flags, red_flags, amber_flags,
                            signal_bundle_id, underwriter_id, policy_id, parent_quote_id,
                            market, broker_code, submission_channel, direct_inquiry,
                            expires_at
                        ) VALUES (
                            %(quote_id)s, %(entity_id)s, %(entity_name)s, %(coverage_type)s,
                            %(model_id)s, %(model_version)s, %(status)s,
                            %(requested_limit)s, %(requested_currency)s, %(effective_date)s,
                            %(term_months)s, %(deductible)s,
                            %(composite_score)s, %(tier)s, %(tier_label)s, %(confidence)s, %(signal_coverage)s,
                            %(gross_premium)s, %(net_premium)s, %(taxes_fees)s, %(rate_per_million)s, %(tier_modifier)s,
                            %(decision_path)s, %(decision_reasons)s, %(green_flags)s, %(red_flags)s, %(amber_flags)s,
                            %(signal_bundle_id)s, %(underwriter_id)s, %(policy_id)s, %(parent_quote_id)s,
                            %(market)s, %(broker_code)s, %(submission_channel)s, %(direct_inquiry)s,
                            %(expires_at)s
                        )
                        ON CONFLICT (quote_id) DO UPDATE SET
                            status = EXCLUDED.status,
                            underwriter_id = EXCLUDED.underwriter_id,
                            policy_id = EXCLUDED.policy_id,
                            updated_at = NOW()
                    """, {
                        **quote_data,
                        "decision_reasons": Json(quote_data.get("decision_reasons")),
                        "green_flags": Json(quote_data.get("green_flags")),
                        "red_flags": Json(quote_data.get("red_flags")),
                        "amber_flags": Json(quote_data.get("amber_flags")),
                        "direct_inquiry": Json(quote_data.get("direct_inquiry")),
                    })
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL save_quote error: {e}")
            return False
    
    def get_quote(self, quote_id: str) -> Optional[Dict]:
        """Get a quote by ID."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM dsi_quotes WHERE quote_id = %s
                    """, (quote_id,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"PostgreSQL get_quote error: {e}")
            return None
    
    def get_quotes_by_entity(self, entity_id: str, limit: int = 100) -> List[Dict]:
        """Get quotes for an entity."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM dsi_quotes
                        WHERE entity_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (entity_id, limit))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"PostgreSQL get_quotes_by_entity error: {e}")
            return []
    
    def get_quote_analytics(self, 
                            start_date: datetime,
                            end_date: datetime,
                            coverage_type: Optional[str] = None) -> Dict:
        """Get quote analytics for a period."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Base query
                    query = """
                        SELECT 
                            COUNT(*) as total_quotes,
                            COUNT(*) FILTER (WHERE status = 'bound') as bound_quotes,
                            COUNT(*) FILTER (WHERE decision_path = 'straight_through') as stp_quotes,
                            AVG(composite_score) as avg_score,
                            AVG(gross_premium) FILTER (WHERE gross_premium IS NOT NULL) as avg_premium,
                            SUM(gross_premium) FILTER (WHERE status = 'bound') as total_bound_premium
                        FROM dsi_quotes
                        WHERE created_at BETWEEN %s AND %s
                    """
                    params = [start_date, end_date]
                    
                    if coverage_type:
                        query += " AND coverage_type = %s"
                        params.append(coverage_type)
                    
                    cur.execute(query, params)
                    row = cur.fetchone()
                    
                    total = row["total_quotes"] or 0
                    return {
                        "period_start": start_date.isoformat(),
                        "period_end": end_date.isoformat(),
                        "total_quotes": total,
                        "bound_quotes": row["bound_quotes"] or 0,
                        "stp_quotes": row["stp_quotes"] or 0,
                        "avg_score": float(row["avg_score"]) if row["avg_score"] else 0,
                        "avg_premium": float(row["avg_premium"]) if row["avg_premium"] else 0,
                        "total_bound_premium": float(row["total_bound_premium"]) if row["total_bound_premium"] else 0,
                        "bind_rate": (row["bound_quotes"] or 0) / total if total > 0 else 0,
                        "stp_rate": (row["stp_quotes"] or 0) / total if total > 0 else 0,
                    }
        except Exception as e:
            logger.error(f"PostgreSQL get_quote_analytics error: {e}")
            return {}
    
    # ==========================================================================
    # Model registry methods
    # ==========================================================================
    
    def save_model(self, model_data: Dict) -> bool:
        """Save a model version."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dsi_models (
                            model_id, version, coverage_type, name, description, status,
                            config, signal_requirements, thresholds, checksum,
                            parent_version, performance_metrics, created_by,
                            activation_date, retirement_date
                        ) VALUES (
                            %(model_id)s, %(version)s, %(coverage_type)s, %(name)s, %(description)s, %(status)s,
                            %(config)s, %(signal_requirements)s, %(thresholds)s, %(checksum)s,
                            %(parent_version)s, %(performance_metrics)s, %(created_by)s,
                            %(activation_date)s, %(retirement_date)s
                        )
                        ON CONFLICT (coverage_type, version) DO UPDATE SET
                            status = EXCLUDED.status,
                            activation_date = EXCLUDED.activation_date,
                            retirement_date = EXCLUDED.retirement_date,
                            performance_metrics = EXCLUDED.performance_metrics
                    """, {
                        **model_data,
                        "config": Json(model_data["config"]),
                        "signal_requirements": Json(model_data["signal_requirements"]),
                        "thresholds": Json(model_data["thresholds"]),
                        "performance_metrics": Json(model_data.get("performance_metrics")),
                    })
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL save_model error: {e}")
            return False
    
    def get_active_model(self, coverage_type: str) -> Optional[Dict]:
        """Get active model for a coverage type."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT m.* FROM dsi_models m
                        JOIN dsi_active_models a ON m.model_id = a.model_id
                        WHERE a.coverage_type = %s
                    """, (coverage_type,))
                    row = cur.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"PostgreSQL get_active_model error: {e}")
            return None
    
    def set_active_model(self, coverage_type: str, model_id: str, version: str) -> bool:
        """Set the active model for a coverage type."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dsi_active_models (coverage_type, model_id, version)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (coverage_type) DO UPDATE SET
                            model_id = EXCLUDED.model_id,
                            version = EXCLUDED.version,
                            activated_at = NOW()
                    """, (coverage_type, model_id, version))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL set_active_model error: {e}")
            return False
    
    # ==========================================================================
    # Audit methods
    # ==========================================================================
    
    def log_audit(self, quote_id: str, action: str, 
                  old_status: Optional[str] = None,
                  new_status: Optional[str] = None,
                  changed_by: Optional[str] = None,
                  reason: Optional[str] = None,
                  metadata: Optional[Dict] = None) -> bool:
        """Log an audit entry for a quote."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dsi_quote_audit (
                            quote_id, action, old_status, new_status,
                            changed_by, change_reason, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (quote_id, action, old_status, new_status, 
                          changed_by, reason, Json(metadata) if metadata else None))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL log_audit error: {e}")
            return False
    
    def get_audit_trail(self, quote_id: str) -> List[Dict]:
        """Get audit trail for a quote."""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM dsi_quote_audit
                        WHERE quote_id = %s
                        ORDER BY created_at ASC
                    """, (quote_id,))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"PostgreSQL get_audit_trail error: {e}")
            return []
    
    # ==========================================================================
    # Cleanup methods
    # ==========================================================================
    
    def cleanup_expired(self) -> int:
        """Remove expired entries from key-value store."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM dsi_kv_store
                        WHERE expires_at IS NOT NULL AND expires_at < NOW()
                    """)
                    deleted = cur.rowcount
                conn.commit()
            logger.info(f"Cleaned up {deleted} expired entries")
            return deleted
        except Exception as e:
            logger.error(f"PostgreSQL cleanup_expired error: {e}")
            return 0
    
    def close(self):
        """Close all connections."""
        self.pool.closeall()
        logger.info("PostgreSQL connections closed")


# Factory function
def create_postgres_storage(config: Dict) -> PostgresStorage:
    """
    Create PostgreSQL storage from configuration dict.
    
    Example config:
        {
            "host": "db.example.com",
            "port": 5432,
            "database": "dsi_production",
            "user": "dsi_app",
            "password": "secret",
            "min_connections": 5,
            "max_connections": 20,
        }
    """
    return PostgresStorage(**config)
