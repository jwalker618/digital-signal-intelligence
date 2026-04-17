# B7 — Political Violence & Terrorism (standalone)

## Path
`coverages/pvt/config.yaml`

## Sub-configs (4)
`pvt_country_risk`, `pvt_sector_exposed`, `pvt_high_value_asset`, `pvt_sme`.

## Signal ID family

Driven by ACLED event density (riot / armed conflict / violence),
GLOBAL TERRORISM DATABASE (GTD) incident overlay, ICRG composite,
sovereign CDS spread proxy, OSAC travel advisory tier, sector
exclusion/embargo overlays, distance-to-critical-asset proximity.

## Sources
ACLED (freemium), GTD (free), World Bank WGI (free), OSAC (free),
ICRG (paid — env-var-gated), OFAC (free).

## Migration
Cross-walks to FPR (`fpr_political_risk`) and Property CAT (CAT-
exposed hard assets) retained as aliases.
