"""V7 Phase 14 — Jinja2 templates for the underwriter disclosure packet.

Kept in code rather than on disk so deployments don't need filesystem
template lookups and so determinism is guaranteed by the import path.
"""

MARKDOWN_TEMPLATE = """\
# Referral Disclosure Packet

**Generated**: {{ p.generated_at }}
**Model version**: `{{ p.model_version_id }}`
**Composite min grade**: `{{ p.composite_min_grade or "n/a" }}`

## Grade distribution
{% for g, w in p.composite_distribution.items() -%}
- {{ g }}: {{ (w * 100) | round(0) | int }}%
{% endfor %}

## Referral reasons
{% for r in p.referral_reasons -%}
- {{ r }}
{% endfor %}

---

{% for s in p.sections %}
## {{ s.title }}

- **Signal**: `{{ s.signal_id }}`
- **Grade**: `{{ s.grade }}`
- **Reproducibility**: `{{ s.reproducibility or "unknown" }}`
- **Commitment**: `{{ s.commitment_digest }}`

### Pro
{{ s.pro }}

### Counter
{{ s.counter }}

### Tie-breaker
{{ s.tie_breaker }}

### Sources
{% for src in s.sources -%}
- `{{ src.kind }}` · `{{ src.source_id }}` · {{ src.ref }} ({{ src.fetched_at }})
{% endfor %}

### Cluster symptoms
{% for sym in s.cluster_symptoms[:5] -%}
- `{{ sym | tojson }}`
{% endfor %}

### Recalled mechanisms
{% for m in s.recalled_mechanisms -%}
- {{ m.summary }} ({{ m.tags | join(", ") }})
{% endfor %}

---
{% endfor %}
"""
