// v8 Phase 8 — portal response types.
//
// Mirror infrastructure/api/routes/portal/schemas.py. Update both
// sides together when the contract changes.

export type ImpactClass = "strength" | "drag" | "neutral";

export interface SignalImpact {
  signal_key: string;
  signal_source: string;
  signal_source_id: string;
  signal_label: string;
  classification: ImpactClass;
  combined_modifier: number;
  premium_delta_usd: number;
  premium_delta_pct: number;
  contributing_modifier_count: number;
}

export interface ImpactBreakdown {
  base_premium: number;
  final_premium: number;
  total_modifier: number;
  strengths: SignalImpact[];
  drags: SignalImpact[];
  neutral: SignalImpact[];
}

export type RemediationEffort = "LOW" | "MEDIUM" | "HIGH";

export interface SignalRemediation {
  headline: string;
  description: string;
  effort: RemediationEffort;
  typical_duration: string;
  typical_cost_usd: number;
  evidence_required: string;
  references: string[];
}

export interface RemediationAction {
  signal_key: string;
  signal_label: string;
  remediation: SignalRemediation;
  estimated_premium_delta_usd: number;
  estimated_premium_delta_pct: number;
  leverage: number;
  is_placeholder: boolean;
}

export interface RemediationPlan {
  actions: RemediationAction[];
  placeholder_count: number;
}

export interface SignalRankEntry {
  signal_id: string;
  entity_value: number;
  cohort_mean: number;
  z_score: number;
}

export interface SignalRanking {
  strengths: SignalRankEntry[];
  weaknesses: SignalRankEntry[];
}

// ----------------------------------------------------------------------------
// /portal/overview
// ----------------------------------------------------------------------------

export interface BrokerInfo {
  id: string;
  name: string;
  slug: string;
}

export interface ClientBookEntry {
  submission_code: string;
  entity_name: string;
  coverage: string;
  status: string;
  composite_score?: number | null;
  tier?: number | null;
  peer_percentile_rank?: number | null;
  recommended_premium?: number | null;
  referral_state?: string | null;
  awaiting_party?: string | null;
  updated_at?: string | null;
}

export interface ClientCoverageEntry {
  submission_code: string;
  coverage: string;
  composite_score?: number | null;
  tier?: number | null;
  peer_percentile_rank?: number | null;
  recommended_premium?: number | null;
  referral_state?: string | null;
  updated_at?: string | null;
}

export interface BrokerOverviewResponse {
  role: "BROKER";
  broker: BrokerInfo;
  clients: ClientBookEntry[];
  open_queries_count: number;
}

export interface ClientOverviewResponse {
  role: "CLIENT";
  entity_name: string;
  broker?: BrokerInfo | null;
  active_coverages: ClientCoverageEntry[];
}

export type OverviewResponse = BrokerOverviewResponse | ClientOverviewResponse;

// ----------------------------------------------------------------------------
// Submission detail
// ----------------------------------------------------------------------------

export interface ScoreResponse {
  submission_code: string;
  coverage: string;
  composite_score?: number | null;
  tier?: number | null;
  base_premium?: number | null;
  final_premium?: number | null;
  impact_breakdown?: ImpactBreakdown | null;
}

export interface PeersResponse {
  submission_code: string;
  coverage: string;
  cohort_id?: string | null;
  cohort_size?: number | null;
  peer_percentile_rank?: number | null;
  cohort_mean_score?: number | null;
  cohort_median_score?: number | null;
  entity_score?: number | null;
  signal_ranking?: SignalRanking | null;
  note?: string | null;
}

export interface ActionsResponse {
  submission_code: string;
  coverage: string;
  remediation_plan: RemediationPlan;
}

export interface QuoteEvolutionEntry {
  quote_code: string;
  version_number: number;
  composite_score?: number | null;
  tier?: number | null;
  final_premium?: number | null;
  created_at: string;
}

export interface ReferralInfo {
  referral_code: string;
  status: string;
  awaiting_party?: string | null;
}

export interface SubmissionDetailResponse {
  submission_code: string;
  entity_name: string;
  coverage: string;
  status: string;
  created_at: string;
  quotes: QuoteEvolutionEntry[];
  referral?: ReferralInfo | null;
}

// ----------------------------------------------------------------------------
// /portal/queries
// ----------------------------------------------------------------------------

export interface OpenQueryEntry {
  referral_code: string;
  submission_code: string;
  entity_name: string;
  coverage: string;
  request_signal_evidence?: string | null;
  open_query_body?: string | null;
  opened_at?: string | null;
}

export interface BrokerQueriesResponse {
  broker: BrokerInfo;
  open_queries: OpenQueryEntry[];
}

// ----------------------------------------------------------------------------
// Broker reply payload
// ----------------------------------------------------------------------------

export interface SignalValueUpdate {
  signal_id: string;
  new_value: boolean | string | number;
  evidence_basis?: string;
}

export interface BrokerReplyRequest {
  body: string;
  signal_value_update?: SignalValueUpdate;
}

export interface BrokerReplyResponse {
  message_id: string;
  triggered_reassessment: boolean;
  new_quote_id?: string | null;
  referral_state: string;
}
