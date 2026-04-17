"""seed.reset — truncate DSI tables in dependency order.

C4-interim ships a placeholder that refuses to run without --confirm
and points at the SQL helper; C4-final wires it into alembic + an
ordered TRUNCATE script.
"""
from __future__ import annotations

import logging
import sys

log = logging.getLogger("seed.reset")


def run(confirm: bool = False) -> int:
    if not confirm:
        print(
            "seed.reset refused — pass --confirm. This wipes every tenant's\n"
            "quotes, submissions, loss events, referrals, and audit logs.",
            file=sys.stderr,
        )
        return 2
    # C4-final will wire this into alembic downgrade + a TRUNCATE script.
    # For C4-interim we defer to operator responsibility.
    print(
        "seed.reset is a placeholder in C4-interim. For now, run:\n"
        "  alembic downgrade base && alembic upgrade head\n"
        "then `python -m seed init` to repopulate."
    )
    return 0
