# DSI Coverage Deployment Guide

Coverage-specific guidance for deploying DSI signal pipelines to production.

## Architecture Summary

DSI uses a **stub/production hybrid** architecture controlled by `FEATURE_USE_STUBS`:
- `stubs`: All extractors return synthetic data (development)
- `production`: Use production extractors where available, stubs as fallback
- `hybrid`: Mixed mode for gradual rollout

**Signal pipeline**: Extractor -> Aggregator -> Categorizer -> Inference Function

Each coverage has:
- **Config**: `coverages/<cov>/config.yaml`
- **Logic docs**: `coverages/<cov>/logic.md`
- **Stubs**: `signal_architecture/signals/extractors/stubs/<cov>/`
- **Aggregators**: `signal_architecture/signals/aggregators/implementations/<cov>/`
- **Inference**: `signal_architecture/signals/inference/functions/<cov>/`

Production extractors are shared: `signal_architecture/signals/extractors/production/` (44 extractors).

## Production Extractor Availability

| Category | Count | Examples |
|-|-|-|
| DNS/Network | 8 | TLS, DNSSEC, email auth, security headers, WAF, CDN |
| SEC/Financial | 5 | 10-K, 10-Q, proxy statements, 8-K disclosures |
| Regulatory | 9 | EPA, OSHA, BSEE, FAA, OFAC |
| Sanctions | 7 | OFAC SDN, EU, UN |
| Corporate | 5 | Security pages, privacy policy, bug bounty |
| Maritime | 2 | Port state control, classification |
| Other | 8 | Security.txt, HTTP headers, IP analysis |

## Coverage-Specific Requirements

### Cyber (11 configs)

`cyber_general, cyber_sme, cyber_healthcare, cyber_financial_services, cyber_critical_infrastructure, cyber_technology, cyber_digital_platform, cyber_manufacturing, cyber_retail, cyber_public_sector, cyber_professional_services`

**Ready now** (free extractors): TLS, security headers, email auth, WAF, CDN, security pages, privacy policy

**Stubs to convert**: `stubs/cyber/` (4 files including phase_7 sector-specific signals)

**Paid dependencies**: SecurityScorecard/BitSight (~$50K/yr), Shodan ($59/mo), HIBP (free non-commercial)

**Verify**: `python -m layers.risk.calibration_harness cyber`

**Logic**: `coverages/cyber/logic.md`

---

### Professional Indemnity (13 configs)

`pi_general, pi_sme, pi_legal_large, pi_legal_specialist, pi_audit, pi_accounting, pi_architecture, pi_engineering, pi_technology, pi_financial_advisory, pi_management_consulting, pi_real_estate, pi_environmental`

**Ready now**: SEC filings (public firms), state licensing checks, corporate footprint

**Stubs to convert**: `stubs/pi/` (4 files including phase_6 profession-specific signals)

**Paid dependencies**: State bar APIs (varies), PCAOB database, professional licensing boards

**Verify**: `python -m layers.risk.calibration_harness pi`

**Logic**: `coverages/pi/logic.md`

---

### Energy (10 configs)

`energy_general, energy_upstream_deepwater, energy_upstream_onshore, energy_upstream_unconventional, energy_midstream, energy_downstream, energy_offshore_wind, energy_onshore_renewable, energy_storage, energy_sme`

**Ready now**: OSHA violations, EPA ECHO, BSEE incidents, SEC filings

**Stubs to convert**: `stubs/energy/` (5 files including phase_5 segment-specific signals)

**Paid dependencies**: PHMSA pipeline data, EIA production data, satellite imagery (~$100K/yr)

**Verify**: `python -m layers.risk.calibration_harness energy`

**Logic**: `coverages/energy/logic.md`

---

### D&O (6 configs)

`do_general, do_sme, do_public, do_pe_backed, do_nonprofit, do_ipo_spac`

**Ready now**: SEC EDGAR (10-K, DEF 14A, 8-K), board composition

**Stubs to convert**: `stubs/do/` (3 files)

**Paid dependencies**: Court records (PACER $0.10/page), D&B corporate data (~$50K/yr)

**Verify**: `python -m layers.risk.calibration_harness do`

---

### Financial Institutions (6 configs)

`fi_general, fi_sme, fi_bank, fi_insurer, fi_fintech, fi_crypto`

**Ready now**: FDIC/OCC exam data, SEC filings, OFAC sanctions

**Stubs to convert**: `stubs/fi/` (3 files)

**Paid dependencies**: FFIEC Call Reports (free), Bloomberg/Refinitiv (~$25K/yr)

**Verify**: `python -m layers.risk.calibration_harness fi`

---

### Marine (7 configs)

`marine_general, marine_sme, marine_cargo, marine_tanker, marine_offshore, marine_war_risk, marine_high_value`

**Ready now**: Port state control, classification society, OFAC sanctions

**Stubs to convert**: `stubs/marine/` (3 files)

**Paid dependencies**: Equasis (free individual), AIS tracking (~$20K/yr)

**Verify**: `python -m layers.risk.calibration_harness marine`

---

### Aerospace (7 configs)

`aerospace_general, aerospace_sme, aerospace_space, aerospace_rotary, aerospace_unmanned, aerospace_mro, aerospace_high_value`

**Ready now**: FAA certificates, EASA SAFA, EU Air Safety List

**Stubs to convert**: `stubs/aerospace/` (6 files)

**Paid dependencies**: OAG schedule data (~$30K/yr)

**Verify**: `python -m layers.risk.calibration_harness aerospace`

---

### Property (5 configs)

`property_general, property_high_value, property_cat_exposed, property_builders_risk, property_sme`

**Ready now**: ISO/COPE construction classifications, FEMA flood zones, ISO public protection class

**Stubs to convert**: `stubs/property/` (3 files)

**Paid dependencies**: CAT modelling (RMS/AIR ~$50K/yr), property valuations

**Verify**: `python -m layers.risk.calibration_harness property`

---

### Casualty (6 configs)

`casualty_gl, casualty_wc, casualty_auto, casualty_umbrella, casualty_environmental, casualty_sme`

**Ready now**: NCCI experience mods, OSHA citations, DOT safety records, EPA enforcement

**Stubs to convert**: `stubs/casualty/` (3 files)

**Paid dependencies**: NCCI class code data (~$15K/yr), ISO CGL rates

**Verify**: `python -m layers.risk.calibration_harness casualty`

---

### Financial & Political Risk (5 configs)

`fpr_trade_credit, fpr_political_risk, fpr_surety, fpr_kidnap_ransom, fpr_sme`

**Ready now**: Sovereign risk ratings, Berne Union data, sanctions screening

**Stubs to convert**: `stubs/fpr/` (3 files)

**Paid dependencies**: Country risk analytics (Verisk Maplecroft ~$25K/yr), credit agency feeds

**Verify**: `python -m layers.risk.calibration_harness fpr`

---

## Pre-Deployment Checklist

1. Run calibration: `python -m layers.risk.calibration_harness` (all pass)
2. Run assessor: `python development/project/assessments/scripts/dsi_assessor.py`
3. Run seed: `python seed_dsi_bench.py` (validates full pipeline)
4. Regenerate docs: `python coverages/doc_generator.py`
5. Set env: `FEATURE_USE_STUBS=production` or `hybrid`
6. Configure API keys for paid data sources
7. Run migrations: `alembic upgrade head`
8. Deploy via `deploy/` configs (Docker/Kubernetes/monitoring)

## Cost Summary

| Tier | Annual Cost | Coverage |
|-|-|-|
| Free | $0 | DNS, SEC, OSHA, EPA, FAA, OFAC, HTTP |
| Low | $5K-$15K | Shodan, HIBP, court records |
| Medium | $50K-$150K | SecurityScorecard, D&B, AIS |
| Premium | $150K-$300K | Bloomberg, satellite, ESG |

Full details: `development/extractor_implementation_plan.md`
