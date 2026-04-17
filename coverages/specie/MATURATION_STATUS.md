# Specie / Fine Art — V6 Maturation Status (B11)

Depth-first build **complete** (Stage 3.10 of the Option-D plan).

| Mature Bar | Current | Status |
|------------|---------|--------|
| 4 sub-configs | 4 | ✅ |
| ≥ 22 signal IDs | 33 | ✅ |
| ≥ 60 inference functions | 33 | ⏳ +27 derived planned |
| Primary config ≥ 40 scored signals | 33 | ⏳ +7 |
| Routing constraints on every sub-config | 4/4 | ✅ |
| Parametric ILF curves per product_type | auto-generated | ✅ |
| Guardrails populated | all 4 sub-configs | ✅ |
| 10 golden entities green | **10** | ✅ |
| `calibrate --coverage specie` returns PASS | **PASS** (768/768) | ✅ |
| `assess_config_compliance` returns 0 errors | **0** | ✅ |

## Routing

| Sub-config | Routes on |
|------------|-----------|
| specie_vault_cash | specie_type == 'vault_cash' |
| specie_jewelry_precious_metals | specie_type == 'jewelry' |
| specie_fine_art_gallery | specie_type == 'fine_art' |
| specie_sme | tiv < 10 000 000 |

## Goldens (10)

Christie's, Sotheby's, Phillips, Bonhams (fine_art_gallery);
Brink's, Loomis (vault_cash); Tiffany, Cartier, Harry Winston
(jewelry); Luminous Gallery (sme).
