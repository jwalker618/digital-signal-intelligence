For an insurance pricing application where auditability, reproducibility, and integrity are paramount, the optimal method is a Content-Addressable Storage (Hybrid) pattern.
This approach ensures that if a model is generated twice with the exact same inputs, it references the same snapshot. If a single parameter changes, it creates a new, distinct snapshot.
The Recommended Architecture: Hybrid Storage
The best practice is to separate the metadata (who, when, what) from the payload (the actual YAML file).For an insurance pricing application where auditability, reproducibility, and integrity are paramount, the optimal method is a Content-Addressable Storage (Hybrid) pattern.
This approach ensures that if a model is generated twice with the exact same inputs, it references the same snapshot. If a single parameter changes, it creates a new, distinct snapshot.
The Recommended Architecture: Hybrid Storage
The best practice is to separate the metadata (who, when, what) from the payload (the actual YAML file).

Step-by-Step Implementation
1. Generate a Content-Based Unique ID (The Hash)
Before saving, hash the YAML content. This acts as a digital fingerprint. If the config changes by even a space, the hash changes.Step-by-Step Implementation
1. Generate a Content-Based Unique ID (The Hash)
Before saving, hash the YAML content. This acts as a digital fingerprint. If the config changes by even a space, the hash changes.

2. The Storage Logic (Python)
Do not overwrite files. Use the hash as the filename. This automatically deduplicates storage—if ten users run the exact same standard GLM model, you only store the YAML file once, but record ten entries in your database.2. The Storage Logic (Python)
Do not overwrite files. Use the hash as the filename. This automatically deduplicates storage—if ten users run the exact same standard GLM model, you only store the YAML file once, but record ten entries in your database.

Why this is the "Best" Method for Insurance:
• Immutable Audit Trail: In technical pricing, you must prove exactly what parameters were used to generate a rate. This method guarantees that Run A used Config Hash X. You can download Config Hash X 5 years later and know for a fact it hasn't been tampered with (because the hash would no longer match).
• Storage Efficiency: Insurance teams often run "sensitivity tests" changing only one small factor. You avoid storing duplicates of the base config.
• Searchability: You can add columns to your Postgres table for high-level tags (e.g., LineOfBusiness, Region) to easily find "All UK Motor models built in 2024," without parsing thousands of YAML files.Why this is the "Best" Method for Insurance:
• Immutable Audit Trail: In technical pricing, you must prove exactly what parameters were used to generate a rate. This method guarantees that Run A used Config Hash X. You can download Config Hash X 5 years later and know for a fact it hasn't been tampered with (because the hash would no longer match).
• Storage Efficiency: Insurance teams often run "sensitivity tests" changing only one small factor. You avoid storing duplicates of the base config.
• Searchability: You can add columns to your Postgres table for high-level tags (e.g., LineOfBusiness, Region) to easily find "All UK Motor models built in 2024," without parsing thousands of YAML files.
