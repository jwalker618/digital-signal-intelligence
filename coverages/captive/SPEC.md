# B12 — Captive / Alternative Risk Transfer (ART)

## Path
`coverages/captive/config.yaml`

## Sub-configs (4)

`captive_single_parent`, `captive_group`, `captive_risk_retention_group`,
`captive_cell_protected`.

## Signal families

Parent financial strength (reuse A5/D&O signals via cross-walk),
domicile regulatory quality (NAIC, Bermuda BMA, Cayman CIMA,
Guernsey/Jersey), captive-manager quality, loss-fund adequacy,
reinsurance chain (B9 cross-walk), fronting-carrier quality,
tax-efficiency band, programme maturity (years in force).

## Sources

All already landed: NAIC I-Site (A5), SEC 10-K for parent (cross-walk),
state captive insurance division public lists, NAIC financial-strength
bands, free Bermuda BMA / Cayman CIMA public lookups.
