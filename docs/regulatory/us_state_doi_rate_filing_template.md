# US State DOI SERFF Rate-Filing Template

**Summary.** DSI ships a rate-filing generator that assembles the
SERFF-ready pack (filing memo, actuarial justification, rate exhibit,
governance statement, cover page) for any (coverage, config, state)
triple.

## Mechanics

```
python -m infrastructure.admin.rate_filing \
    --coverage cyber --config cyber_general --state IL \
    --out filings/IL_cyber_2026Q2/
```

See `infrastructure/admin/rate_filing.py` for the generator.

## Initial filings

| State | Coverages | Status |
|-------|-----------|--------|
| IL | Cyber, FI | **Q4 target** |
| CA | Cyber, FI, D&O, Casualty GL | Q4 target |
| TX | Cyber, FI, Property (CAT-exposed), Casualty GL | Q4 target |

## Gaps

| Gap | Owner | Due |
|-----|-------|-----|
| External actuarial certification on each filing | Chief Actuary + external | 2026-Q4 |
| Counsel review of memo template | Legal | 2026-Q3 |
| PDF rendering (currently `.txt` cover) | Platform | 2026-Q4 |
