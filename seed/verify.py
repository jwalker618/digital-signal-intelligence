"""seed.verify — assert expected post-seed row counts.

C4-interim ships a minimal probe that checks a few headline tables.
C4-final moves the counts into a YAML contract under seed/fixtures/.
"""
from __future__ import annotations

import logging
import sys
from typing import Dict

log = logging.getLogger("seed.verify")

EXPECTED_MIN_COUNTS: Dict[str, int] = {
    "coverage_versions": 10,
    "submissions": 50,
    "quotes": 50,
    "tenants": 1,
    "users": 3,
}


def run() -> int:
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        log.error("sqlalchemy not installed")
        return 2

    import os
    url = os.environ.get("DATABASE_URL")
    if not url:
        log.error("DATABASE_URL is not set")
        return 2

    engine = create_engine(url)
    mismatches = []
    with engine.connect() as conn:
        for table, min_count in EXPECTED_MIN_COUNTS.items():
            try:
                actual = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            except Exception as e:
                mismatches.append(f"{table}: query failed — {e}")
                continue
            if actual < min_count:
                mismatches.append(f"{table}: {actual} < {min_count}")

    if mismatches:
        for m in mismatches:
            print(f"FAIL {m}", file=sys.stderr)
        return 1
    print("seed.verify: all minimum row counts satisfied.")
    return 0
