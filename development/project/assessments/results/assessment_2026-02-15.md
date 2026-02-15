======================================================================
DSI CHECKLIST ASSESSMENT REPORT
======================================================================

Assessment Date: 2026-02-15
Assessed By: assess.py (Automated - Phase 7.1)
Codebase Stats: 301 Python files, 94768 lines, 7 coverages, 13 configurations

Section Scores:
  coverages:            299 / 364 items
  demo:                   3 /   3 items
  deploy:                11 /  11 items
  docs:                   9 /   9 items
  infrastructure:         4 /   5 items
  layers:                11 /  11 items
  rust:                   6 /   6 items
  schemas:                2 /   4 items
  signal_architecture:   11 /  11 items
  tests:                  4 /   4 items

Overall: 360 / 428 items (86.2%)

Per-Coverage Configuration Status:
--------------------------------------------------
  aerospace_general         24/28 checks  [3 FAIL]
  aerospace_sme             24/28 checks  [3 FAIL]
  cyber_general             24/28 checks  [3 FAIL]
  cyber_sme                 23/28 checks  [4 FAIL]
  do_general                24/28 checks  [3 FAIL]
  do_sme                    23/28 checks  [3 FAIL]
  energy_general            24/28 checks  [3 FAIL]
  fi_general                23/28 checks  [3 FAIL]
  fi_sme                    23/28 checks  [4 FAIL]
  marine_general            24/28 checks  [3 FAIL]
  marine_sme                23/28 checks  [4 FAIL]
  pi_general                24/28 checks  [3 FAIL]
  pi_sme                    16/28 checks  [10 FAIL]

Top Gaps:
1. [coverages] aerospace_general: inference_functions
   -> Missing 47 functions
2. [coverages] aerospace_general: group_ids_match
   -> Invalid group refs: operator_type: operator_type, fleet_category: fleet_category, fleet_size: fleet_size
3. [coverages] aerospace_general: exposure_bands
   -> No exposure size_bands
4. [coverages] aerospace_sme: inference_functions
   -> Missing 22 functions
5. [coverages] aerospace_sme: group_ids_match
   -> Invalid group refs: operator_type: operator_type, fleet_category: fleet_category, fleet_size: fleet_size

Recommended Next Steps:
1. Address 49 failing checks in coverages
2. Address 49 failing checks in coverage configs
3. Address 1 failing checks in infrastructure

======================================================================