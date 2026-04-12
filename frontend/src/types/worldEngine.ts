// FE: World Engine types.

export type MaturityStage =
  | "DISCOVERY"
  | "CALIBRATION"
  | "VALIDATION"
  | "OPERATIONAL"
  | "MATURE";

export interface MaturityState {
  stage: MaturityStage;
  assessed_entity_count: number;
  active_relationships: number;
  coverage_ratio: number;
  min_entities_for_next_stage: number;
}

export interface RelationshipRow {
  id: string;
  source_entity: string;
  target_entity: string;
  relationship_type: string;
  strength: number;
  confidence: number;
  evidence_count: number;
  status: string;
  created_at: string;
}

export interface DriftAlert {
  id: string;
  signal_id: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  drift_type: string;
  summary: string;
  detected_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
}

export interface WorldEngineStats {
  total_relationships: number;
  active_relationships: number;
  inactive_relationships: number;
  drift_alerts_open: number;
  assessed_entities: number;
}
