# ${\color{blue}Digital\space Signal\space Intelligence\space (DSI)}$

## Data Persistence Architecture

| Item | Value |
|-|-|
|Version|2.0|
|Date|November 2025|
|Classification|Technical Specification|

---

### Overview
When a technical model is generated:
  - the completed selected configuration is persisted. This allows the model to be generated at any moment based on its original specification
    - note: test profiles are removed as these are extraneous.
  - every item with an id is captured in a seperate file with the associated return and persisted after a complete interaction  - this is a model version

This document explains exactly how that process works.

### Treatment of the payload (underlying YAML configuration) and creation metatdata

DSI uses a Content-Addressable Storage (Hybrid) pattern. 
This is vital to a technical pricing application where auditability, reproducibility, and integrity are paramount. 

Specifically, the implementation is as follows:   
  **Stage 1/.**
  - when a model is generated the underlying YAML configuration payload is converted into a SHA-256 hash.
    - note: this ensures the unique integrity of each snapshot as even if a single parameter changes, even by a space, the hash changes.
  - if the unique hash has not been saved previously it is now persisted into s3 storage (be that Azure, AWS, or GCP).
  - if the unique hash already exists no action is taken, which prevents duplication, and move to Stage 2.

  **Stage 2/.**
  - the metadata (creating user, time, unique ID etc) are saved into structured storage - for example, postgresql.

This approach means there will inevitably be more metatdata records than payloads: ie. it ensures maximum efficiency.

#### Why this is the "Best" Method:
• **Immutable Audit Trail**: In technical pricing, you must prove exactly what parameters were used to generate a rate. This method guarantees that Run A used Config Hash X. You can download Config Hash X 5 years later and know for a fact it hasn't been tampered with (because the hash would no longer match).
• **Storage Efficiency**: Insurance teams often run "sensitivity tests" changing only one small factor. You avoid storing duplicates of the YAML configuration.
• **Searchability**: You can add columns to your structured storage table for high-level tags (e.g., LineOfBusiness, Region) to easily find "All UK Motor models built in 2024," without parsing thousands of YAML files.

### Treatment of model interactions
