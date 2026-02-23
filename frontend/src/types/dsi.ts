export type DecisionType = 'approve' | 'refer' | 'decline';

export interface SignalCondition {
  signal_id: string;
  action: DecisionType | 'modifier';
  note: string;
  applied_modifier?: number;
}

export interface ModelVersion {
  version_id: string;
  composite_score: number;
  confidence: number;
  final_tier: number;
  tier_label: string;
  base_premium: number;
  final_premium: number;
  decision: DecisionType;
  auto_approve: boolean;
  referral_reasons: string[];
  signal_conditions: SignalCondition[];
}

export interface Submission {
  submission_id: string;
  entity_name: string;
  discovered_domain: string;
  coverage: string;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  latest_model_version?: ModelVersion;
}