# V10 Phase 9 — Root-Cause Clusters & Primitive Lenses

**Status:** Planning
**Depends on:** Phase 2 (carrier evidence drawer exposes `cluster_id`/`primitive_type`), Phase 6/7 (client/broker surfaces)
**Audience:** carrier (full) → client/broker (simplified "themes")
**Backend precondition:** none for carrier (`cluster_id`/`primitive_type` inline); client/broker get a clustered-themes projection (small addition to Phase 1's endpoint).

The evidence engine already groups correlated findings into root-cause clusters and tags each signal with one of 12 primitive types. Surfacing these turns a long flat list of signals into a small set of **themes** — far more digestible for every audience, and the basis of the disclosure packet's grouping.

---

## A. What has been built (backend)
- Root-cause clusters: `signal_architecture/signals/routing/root_cause_cluster.py`; exposed inline as `SignalEvidenceDTO.cluster_id` and grouped in the disclosure `payload.sections[].cluster_symptoms`.
- Primitive classification (12): `signal_architecture/signals/primitive_classification.py`; inline `SignalEvidenceDTO.primitive_type` and `CompositeEvidenceDTO.per_primitive` rollup.
- Variants: `variant_of` inline (single-hop amplification).

### A.1 Small backend addition
Extend Phase 1's `/portal/submissions/{code}/evidence` with an optional `group_by=cluster|primitive` that returns signals bucketed into **themes** with a neutral, audience-safe `theme_label` (derived from primitive/cluster, no internal ids leaked to client). Carrier keeps raw `cluster_id`/`primitive_type`.

---

## B. What it augments & why
Augments the **carrier risk table** (Phase 2) with cluster grouping + a primitive lens, and the **client drivers** / **broker workbench** with a themed rollup. Why: a submission can have 30+ signals; presenting them as ~6 root-cause themes ("Access control", "Patch hygiene", "Financial distress") is how a human actually reasons. Clusters also de-duplicate correlated symptoms so the same underlying weakness isn't double-counted in the client's mind. The `per_primitive` rollup answers "where is my evidence weakest *by category*."

---

## C. Frontend implementation

### C.1 Carrier (full)
- **Cluster grouping** in the risk table: a toggle "group by root cause" collapses rows by `cluster_id`; each cluster header shows the cluster's worst grade + member count; `<ClusterChip>` (stub from Phase 2) becomes interactive.
- **Primitive lens**: a view over `CompositeEvidenceDTO.per_primitive` — a `charts/` rollup of grade distribution per primitive type (which categories are well- vs thinly-evidenced).
- **Variant indicator**: signals with `variant_of` shown nested under their parent (amplified variants).

### C.2 Client (simplified themes)
- **`client/drivers`**: a `group_by=primitive` toggle rendering findings under neutral `theme_label`s, each theme with a `<CompositeGradeRollup>`. No raw cluster/primitive ids. This makes "what should I focus on" obvious: themes sorted by impact × low-evidence.

### C.3 Broker (themes + fragility)
- **`broker/clients/...`**: themed rollup per client; cross-client, the most common weak themes across the book (feeds the broker's coaching priorities; complements Phase 7's fragility index).

### C.4 Per-audience matrix
| | Client | Broker | Carrier |
|---|---|---|---|
| theme grouping (neutral labels) | ✅ | ✅ | ✅ |
| raw `cluster_id` / `primitive_type` | ❌ | ❌ | ✅ |
| per-primitive grade distribution | ❌ | book-level | ✅ |
| variant nesting | ❌ | ❌ | ✅ |

---

## D. States
- Signals without a cluster: an "Ungrouped" bucket, never hidden.
- Single-cluster submission: grouping toggle still works (one group).

## E. Definition of done
- Carrier risk table groups by root cause and offers a primitive lens; variants nest under parents.
- `group_by` param added to the portal evidence projection; client/broker render neutral themes with rollups.
- No raw cluster/primitive ids in client/broker DOM.
