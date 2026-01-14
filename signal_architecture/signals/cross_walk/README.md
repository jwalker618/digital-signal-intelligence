# Coverage Crosswalk

## 📘 Overview
This repository contains a **normalized crosswalk** of coverage IDs across seven domains:

- Aerospace  
- Cyber  
- Directors & Officers (DO)  
- Energy  
- Financial Institutions (FI)  
- Professional Indemnity (PI)  
- Marine  

The crosswalk aligns **common concepts** (e.g., Credit Rating, Leadership Stability, Regulatory Actions) with their corresponding **full path IDs** in each coverage schema.  

---

## 🗂️ File Contents
- **`coverage_crosswalk.json`**  
  - Contains structured mappings of `commonConcept` → coverage IDs.  
  - Each coverage entry uses **full path IDs** (e.g., `signal_features/financial_stability/credit_rating`) to avoid collisions.  
  - Metadata includes description, notes, version, and last updated date.  

---

## 🔑 Key Design Principles
- **Full Path IDs**: Prevent ambiguity by including the entire hierarchy.  
- **Common Concepts**: Provide a normalized anchor for mapping across coverages.  
- **Empty Arrays**: Indicate no equivalent ID exists in that coverage.  
- **Extensibility**: New coverages or concepts can be added without breaking structure.  
- **LLM‑Friendly**: JSON format ensures easy parsing and interrogation by AI models.  

---

## 📊 Example Structure
```json
{
  "commonConcept": "Credit Rating",
  "aerospace": ["signal_features/financial_stability/credit_rating"],
  "cyber": ["signal_features/structured_data/credit_rating"],
  "do": ["signal_features/structured_data/credit_rating"],
  "energy": [
    "signal_features/financial_stability/credit_rating",
    "signal_features/structured_data/credit"
  ],
  "fi": [
    "signal_features/network_authority/credit_rating",
    "signal_features/structured_data/credit_rating_structured"
  ],
  "pi": ["signal_features/firm_stability/financial_stability"],
  "marine": ["signal_features/structured_data/credit_rating"]
}
