"""`python -m seed <command>` CLI (V6/C4).

Commands
--------
init        Run reset → bench → v5 → synthetic in order.
bench       Legacy seed_dsi_bench content (via seed.bench).
v5          Legacy seed_v5 content (via seed.v5).
synthetic   Legacy synthetic_generator content (via seed.synthetic).
reset       Placeholder (C4-interim). --confirm required.
verify      Assert post-seed row counts against EXPECTED_MIN_COUNTS.
demo-reset  v8 Phase 7: deterministic state for the client portal demo.
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import bench, demo_reset, reset, synthetic, v5, verify


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m seed")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="reset → bench → v5 → synthetic")
    init.add_argument("--tenant", default="dsi-demo")
    init.add_argument("--entities", type=int, default=1000)
    init.add_argument("--skip-reset", action="store_true")

    sub.add_parser("bench", help="run the bench seed")
    sub.add_parser("v5", help="run the v5 companion seed")

    syn = sub.add_parser("synthetic", help="run the synthetic generator")
    syn.add_argument("--coverage", default=None)
    syn.add_argument("--n", type=int, default=1000)

    rst = sub.add_parser("reset", help="truncate DSI tables (requires --confirm)")
    rst.add_argument("--confirm", action="store_true")

    sub.add_parser("verify", help="assert expected row counts")

    dr = sub.add_parser(
        "demo-reset",
        help="v8 Phase 7: reset to the client portal demo Act 1 state",
    )
    dr.add_argument("--password", default=None,
                    help="override DSI_DEMO_PASSWORD env var")
    dr.add_argument("--rng-seed", type=int, default=None,
                    help="override DSI_DEMO_RNG_SEED env var")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    cmd = args.command
    if cmd == "init":
        if not args.skip_reset:
            rc = reset.run(confirm=True)
            if rc != 0:
                return rc
        for step, fn in (("bench", bench.run), ("v5", v5.run)):
            print(f"[seed init] step: {step}")
            rc = fn()
            if rc != 0:
                print(f"[seed init] {step} failed with {rc}", file=sys.stderr)
                return rc
        print(f"[seed init] step: synthetic (n={args.entities})")
        rc = synthetic.run(n=args.entities)
        return rc
    if cmd == "bench":
        return bench.run()
    if cmd == "v5":
        return v5.run()
    if cmd == "synthetic":
        return synthetic.run(coverage=args.coverage, n=args.n)
    if cmd == "reset":
        return reset.run(confirm=args.confirm)
    if cmd == "verify":
        return verify.run()
    if cmd == "demo-reset":
        return demo_reset.run(
            password=args.password, rng_seed=args.rng_seed,
        )
    raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    sys.exit(main())
