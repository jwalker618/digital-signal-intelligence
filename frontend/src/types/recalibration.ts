// FE: Recalibration + Loss types.

export type ProposalStatus =
  | "DRAFT"
  | "PENDING_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "DEPLOYED";

export interface ProposalSummary {
  id: string;
  coverage: string;
  config_name: string;
  status: ProposalStatus;
  proposed_at: string;
  proposed_by: string;
  trigger: string;
  sample_size: number;
  weight_change_count: number;
  tier_change_count: number;
  reviewer_id: string | null;
  reviewed_at: string | null;
  deployed_at: string | null;
}

export interface WeightChange {
  signal_id: string;
  current_weight: number;
  proposed_weight: number;
  rationale: string;
}

export interface TierThresholdChange {
  band_id: number;
  boundary: "min" | "max";
  current_value: number;
  proposed_value: number;
  rationale: string;
}

export interface ProposalDetail extends ProposalSummary {
  signal_report_cards: unknown[];
  weight_changes: WeightChange[];
  tier_threshold_changes: TierThresholdChange[];
  impact_assessment: Record<string, unknown>;
  statistical_evidence: Record<string, unknown>;
  review_decision: string | null;
  review_rationale: string | null;
  deployed_config_version_id: string | null;
}

export interface LossEvent {
  id: string;
  tenant_id: string;
  entity_name: string;
  coverage: string;
  event_date: string;
  gross_amount: number;
  net_amount: number | null;
  cause_code: string | null;
  status: string;
  quote_id: string | null;
  assessment_id: string | null;
  ingested_at: string;
}
