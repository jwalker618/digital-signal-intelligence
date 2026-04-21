// FE: World Engine types.
//
// Mirror the backend types in world_engine/types.py and the API
// responses defined in world_engine/registry/types.py.

export type MaturityStage = "seed" | "learn" | "emerge" | "simulate";

export type LifecycleState =
  | "candidate"
  | "provisional"
  | "active"
  | "deprecated";

export type DriftSeverity = "info" | "warning" | "critical";

export type CausalDirection =
  | "a_causes_b"
  | "b_causes_a"
  | "bidirectional"
  | "contemporaneous";

export interface MaturityState {
  stage: MaturityStage;
  assessed_entity_count: number;
  entities_with_temporal_data: number;
  earliest_assessment: string | null;
  time_depth_months: number;
  active_relationships: number;
  provisional_relationships: number;
  candidate_relationships: number;
  capabilities: Record<string, boolean>;
  evaluated_at: string;
}

export interface DiscoveredRelationship {
  id: string;
  source_signal: string;
  target_signal: string;
  direction: CausalDirection;
  lag_months: number | null;
  correlation_rho: number;
  effect_size: number;
  influence_weight: number;
  population_size: number;
  lifecycle_state: LifecycleState;
  state_entered_at: string;
  created_at: string;
  updated_at: string;
}

export interface DriftAlert {
  id: string;
  alert_type: string;
  severity: DriftSeverity;
  source_signal: string | null;
  target_signal: string | null;
  relationship_id: string | null;
  description: string;
  evidence: Record<string, unknown>;
  detected_at: string;
  acknowledged: boolean;
  acknowledged_at: string | null;
}

/** Mirrors EngineStatsResponse from world_engine/registry/types.py. */
export interface WorldEngineStats {
  maturity: MaturityState;
  relationships_by_state: Record<string, number>;
  scan_runs_total: number;
  scan_runs_last_7_days: number;
  drift_alerts_unacknowledged: number;
  consistency_scores_total: number;
  caf_computations_total: number;
  evaluated_at: string;
}
