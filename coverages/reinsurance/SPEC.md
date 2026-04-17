# B9 — Reinsurance Treaty & Fac

## Path
`coverages/reinsurance/config.yaml`

## Sub-configs (5)

`reins_treaty_proportional`, `reins_treaty_excess_of_loss`,
`reins_treaty_aggregate`, `reins_facultative`, `reins_sme`.

## Key signal families

Cedent portfolio mix, cat bond exposure overlay, historical loss
triangles, cedent governance (inherits D&O signals via cross-walk),
retrocession chain depth, collateral quality, sidecar participation,
A+/AA+ rating mix, NAIC RBC for US cedents, Solvency II SCR for EU.

## Cedent cross-walk

Cedent signals imported from whichever ceding coverage the cession
applies to (Property CAT → cat signals; Casualty GL → GL signals;
Cyber → cyber signals). `cedent_cross_walk.yaml` documents the
mapping.

## Sources

All already landed: NAIC I-Site (A5), AM Best free rating summaries,
Solvency II public disclosures, SEC 10-K schedule P for US P&C.
