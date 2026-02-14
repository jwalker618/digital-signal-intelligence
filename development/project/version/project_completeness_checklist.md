# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## A New Information Substrate for Insurance

| Item | Value |
|-|-|
|Version|0.1.0|
|Date|January 2025|
|Classification|Configuration Architecture|

---

# coverages (coverages/)
- Is there a logic.md file for every config.yaml file which explains then logic / decision making used?
  - Does this include each configuration under the config?
  - Does this show risk, loss, and exposure weights that add to 1? (Test)
- Is the premium-methodology used by each configuration correct? (Test)
  - PREMIUM_BASE (Fixed Price) should be used for high volume / low variance profile risks, where a multiplier would add un-neccessary complexity.
      - For example, SME / Micro business schemes (e.g., turnover < $5M)
      - For example, Liability-Driven Lines where the maximum possible loss is capped strictly by the Policy Limit (not the client's asset size)
  - MULTIPLIER (Rate × Basis) should be used for lines where the Exposure Basis scales significantly (10x+) or where the asset is the insurance object.
      - For example, First-Party Property (Energy, Aerospace, Marine), where the kimit is often equal ot the TIV.
      - For example, A Hedge Fund's exposure is directly correlated to Assets Under Management (AUM).
      - For example, Mid-Market to Enterprise Cyber.
- Is the config.yaml and all underlying configurations compliant with the master_config_layout? (Test)
    - Are all components included? This should include: direct_queries, signal_registry, risk_tier_bands, loss_tier_bands, exposure, limit_bandings, pricing (including a correct anchor)


# demo (demo/)
- does the demo work? 
- do all examples work?

# deploy (deploy/)
- Is the deployment_guide.md comprehensive and include all neccessary steps to deploy DSI?

# docs (docs/overview/)
- Is the project correctly reflective of the whitepaper?
- Is the project correctly reflective of the visionpaper?

# infrastructure (infrastructure/)

# layers (layers/)

# rust (rust/)

# schemas (schemas/)

# signal_architecture (signal_architecture/)

# tests (tests/)
