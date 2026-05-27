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
  // v8.1: loss + exposure + ROL recommendations
  loss_propensity_score?: number | null;
  severity_propensity_score?: number | null;
  loss_propensity_band?: string | null;
  loss_trend_direction?: string | null;
  exposure_value?: number | null;
  exposure_band_label?: string | null;
  exposure_size_score?: number | null;
  exposure_complexity_score?: number | null;
  rol_upper_limit?: number | null;
  rol_upper_premium?: number | null;
  rol_lower_limit?: number | null;
  rol_lower_premium?: number | null;
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
// Communications (list + thread)
// ----------------------------------------------------------------------------

export interface CommunicationItem {
  referral_code: string;
  submission_code: string;
  entity_name: string;
  coverage: string;
  policy_label?: string | null;
  status: string;
  awaiting_party?: string | null;
  last_message_at?: string | null;
  last_message_direction?: string | null;
  last_message_excerpt?: string | null;
  request_signal_evidence?: string | null;
  is_open: boolean;
}

export interface CommunicationsListResponse {
  role: string;
  items: CommunicationItem[];
  open_count: number;
}

export interface CommunicationThreadMessage {
  id: string;
  direction: string;
  body: string;
  request_signal_evidence?: string | null;
  signal_value_update?: Record<string, unknown> | null;
  triggered_reassessment: boolean;
  new_quote_id?: string | null;
  created_at: string;
}

export interface CommunicationsThreadResponse {
  referral_code: string;
  submission_code: string;
  entity_name: string;
  coverage: string;
  policy_label?: string | null;
  status: string;
  awaiting_party?: string | null;
  reasons: string[];
  messages: CommunicationThreadMessage[];
}

// ----------------------------------------------------------------------------
// v8.1: profile, coverage requests, broker recommendations
// ----------------------------------------------------------------------------

export interface ClientProfileResponse {
  entity_name: string;
  broker_name?: string | null;
  industry_code?: string | null;
  industry_label?: string | null;
  revenue_band?: string | null;
  revenue?: number | null;
  domain?: string | null;
  country?: string | null;
  naics_code?: string | null;
  active_coverage_count: number;
  coverage_lines: string[];
  signal_categories_observed: string[];
  signal_categories_pending: string[];
}

export interface CoverageRequestPayload {
  coverage: string;
  desired_limit?: number | null;
  desired_effective_date?: string | null;
  rationale?: string;
}

export interface CoverageRequestResponse {
  request_code: string;
  submission_code: string;
  referral_code: string;
  status: string;
}

export interface BookGapRecommendation {
  client_entity_name: string;
  coverage: string;
  rationale: string;
  estimated_premium_range_usd: [number, number];
  industry_label?: string | null;
}

export interface BrokerRecommendationsResponse {
  broker_name: string;
  recommendations: BookGapRecommendation[];
}

export interface SendRecommendationPayload {
  client_entity_name: string;
  coverage: string;
  message: string;
}

export interface SendRecommendationResponse {
  submission_code: string;
  referral_code: string;
  status: string;
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
