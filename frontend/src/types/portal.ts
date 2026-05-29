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

export interface ScoreHistoryPoint {
  version_number: number;
  composite_score: number;
  created_at: string;
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
  // Phase B1: peer cohort + score history + exposure context.
  peer_cohort_median_score?: number | null;
  peer_cohort_size?: number | null;
  peer_cohort_top_decile?: number | null;
  peer_cohort_min?: number | null;
  peer_cohort_max?: number | null;
  previous_composite_score?: number | null;
  score_history?: ScoreHistoryPoint[] | null;
  exposure_value?: number | null;
  exposure_band_label?: string | null;
  exposure_size_score?: number | null;
  exposure_value_prior?: number | null;
  // Phase B2: loss-outlook summary off the latest MV row, plus a
  // 12-quarter incurred-loss strip aggregated from loss_events
  // (oldest -> newest, normalised so max = 1.0).
  loss_propensity_band?: string | null;
  loss_trend_direction?: string | null;
  loss_frequency_velocity?: number | null;
  loss_severity_velocity?: number | null;
  loss_event_quarters?: number[] | null;
  // Phase F.2: policy facts for the Coverages table.
  limit?: number | null;
  deductible?: number | null;
  aggregate_limit?: number | null;
  expires_at?: string | null;
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
// v8.2 — broker intelligence
// ----------------------------------------------------------------------------

export interface VerticalSummary {
  slug: string;
  name: string;
  icon: string;
  summary: string;
  priority_lines: string[];
  client_count: number;
  policy_count: number;
  premium_total_usd: number;
}

export interface VerticalListResponse {
  verticals: VerticalSummary[];
}

export type AppetiteStance = "leaning_in" | "neutral" | "selective" | "leaning_out";
export type PricingPosition = "tight" | "median" | "light";
export type EsgStance = "leader" | "progressive" | "neutral" | "restrictive";

export interface CarrierSummary {
  slug: string;
  name: string;
  type: string;
  headquarters: string;
  capacity_band: string;
  typical_commission_pct: number;
  pricing_position: PricingPosition;
  esg_stance: EsgStance;
  win_rate: number;
  specialties: string[];
  movement_note: string;
  appetite_summary: Record<string, AppetiteStance>;
}

export interface CarrierRosterResponse {
  carriers: CarrierSummary[];
}

export interface CarrierAppetiteEntry {
  coverage: string;
  stance: AppetiteStance;
}

export interface CarrierDetailResponse {
  summary: CarrierSummary;
  appetite: CarrierAppetiteEntry[];
  esg_note: string;
  movement_note: string;
  your_hit_rate_pct: number;
  your_premium_placed_usd: number;
  your_recent_lines: string[];
}

export interface ClientHealthEntry {
  entity_name: string;
  vertical_slug?: string | null;
  vertical_name?: string | null;
  policy_count: number;
  total_premium_usd: number;
  engagement_score: number;
  engagement_label: string;
  months_since_last_message?: number | null;
  avg_response_hours?: number | null;
  open_query_count: number;
  opportunity_flags: string[];
  risk_flags: string[];
  next_renewal_in_days?: number | null;
}

export interface ClientHealthResponse {
  broker_name: string;
  clients: ClientHealthEntry[];
}

export interface CarrierMatch {
  slug: string;
  name: string;
  suitability_score: number;
  appetite_stance: AppetiteStance;
  predicted_premium_low: number;
  predicted_premium_high: number;
  typical_commission_pct: number;
  pricing_position: PricingPosition;
  esg_stance: EsgStance;
  win_rate_pct: number;
  rationale: string;
}

export interface PlacementStrategyResponse {
  submission_code: string;
  entity_name: string;
  coverage: string;
  carrier_matches: CarrierMatch[];
  placement_note: string;
}

export interface MarketLineSummary {
  slug: string;
  name: string;
  cycle_position: string;
  rate_change_yoy_pct: number;
  capacity_state: string;
  capacity_trend: string;
  loss_trend: string;
  esg_overlay: string;
}

export interface LossEventEntry {
  headline: string;
  line: string;
  date: string;
  estimated_industry_loss_usd_bn: number;
  implication: string;
}

export interface MarketPulseResponse {
  lines: MarketLineSummary[];
  recent_loss_events: LossEventEntry[];
  climate_pulse_summary: string;
  cycle_overall: string;
}

export interface LineDetailResponse {
  slug: string;
  name: string;
  cycle_position: string;
  rate_change_yoy_pct: number;
  capacity_state: string;
  capacity_trend: string;
  loss_trend: string;
  summary: string;
  key_drivers: string[];
  esg_overlay: string;
  top_carriers: CarrierSummary[];
  recent_loss_events: LossEventEntry[];
}

export interface BookHealthResponse {
  broker_name: string;
  client_count: number;
  policy_count: number;
  total_premium_usd: number;
  total_estimated_commission_usd: number;
  avg_lines_per_client: number;
  avg_premium_per_client: number;
  retention_rate_pct: number;
  cross_sell_ratio_pct: number;
  avg_tenure_months: number;
  lines_concentration: Record<string, number>;
  vertical_concentration: Record<string, number>;
  lines_premium: Record<string, number>;
  vertical_premium: Record<string, number>;
  commission_yield_pct: number;
}

export interface CatPerilExposure {
  peril_slug: string;
  peril_name: string;
  exposed_policy_count: number;
  exposed_premium_usd: number;
  relative_severity: number;
  most_exposed_verticals: string[];
}

export interface ConcentrationEntry {
  dimension: string;
  value: string;
  share_pct: number;
  count: number;
  note?: string | null;
}

export interface AggregationResponse {
  broker_name: string;
  total_premium_usd: number;
  industry_concentration: ConcentrationEntry[];
  line_concentration: ConcentrationEntry[];
  cat_peril_exposure: CatPerilExposure[];
  diversification_score: number;
  diversification_note: string;
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

// -----------------------------------------------------------------------------
// /portal/clients/{entity} — broker Client Workbench (revised pack cw_*)
// -----------------------------------------------------------------------------

export interface ClientWorkbenchCoverage {
  code: string;
  line: string;
  carrier?: string | null;
  score?: number | null;
  pure?: number | null;
  tier?: number | null;
  tier_label?: string | null;
  decision?: string | null;
  confidence?: number | null;
  percentile?: number | null;
  cohort_median?: number | null;
  cohort_top_decile?: number | null;
  cohort_size?: number | null;
  premium?: number | null;
  recommended?: number | null;
  limit?: number | null;
  deductible?: number | null;
  status: string;
  status_tone: string;
  signal_coverage?: number | null;
  awaiting?: string | null;
  prev_score?: number | null;
  sir_amount?: number | null;
  sir_applies?: boolean | null;
  waiting_period_hours?: number | null;
  aggregate_limit?: number | null;
  reinstatements?: number | null;
  reinstatement_rate?: number | null;
  coverage_trigger?: string | null;
  extensions_count?: number | null;
  exclusions_count?: number | null;
  sub_limits_label?: string | null;
  loss_propensity_band?: string | null;
  loss_combined_modifier?: number | null;
  loss_frequency_multiplier?: number | null;
  loss_severity_multiplier?: number | null;
  loss_frequency_velocity?: number | null;
  loss_severity_velocity?: number | null;
  loss_confidence?: number | null;
  loss_cohort_name?: string | null;
  loss_trend_direction?: string | null;
  exposure_value?: number | null;
  exposure_band_label?: string | null;
  exposure_size_score?: number | null;
  exposure_complexity_score?: number | null;
  exposure_modifier?: number | null;
  exposure_value_prior?: number | null;
  exposure_bands?: ClientWorkbenchBand[] | null;
  base_premium?: number | null;
  net_premium?: number | null;
  gross_premium?: number | null;
  offered_premium?: number | null;
  total_taxes?: number | null;
  total_commission?: number | null;
  brokerage_rate?: number | null;
  distribution_type?: string | null;
  signed_line?: number | null;
  role?: string | null;
  lead_loading_factor?: number | null;
  modifier_chain?: ClientWorkbenchModifier[] | null;
  impact?: ClientWorkbenchImpact[] | null;
  score_history?: ScoreHistoryPoint[] | null;
}

export interface ClientWorkbenchModifier {
  group: string;
  factor?: number | null;
  delta?: number | null;
  running?: number | null;
}

export interface ClientWorkbenchImpact {
  label: string;
  delta: number;
  direction: "up" | "down";
}

export interface ClientWorkbenchBand {
  label: string;
  min_value?: number | null;
  max_value?: number | null;
  modifier?: number | null;
  active: boolean;
}

export interface ClientWorkbenchMessage {
  direction: "carrier" | "broker";
  who: string;
  body: string;
  at?: string | null;
  signal?: string | null;
}

export interface ClientWorkbenchThread {
  referral_code: string;
  line: string;
  carrier?: string | null;
  awaiting?: string | null;
  ask?: string | null;
  messages: ClientWorkbenchMessage[];
}

export interface ClientWorkbenchLossEvent {
  date?: string | null;
  line: string;
  incurred?: number | null;
  paid?: number | null;
  cause?: string | null;
  status?: string | null;
}

export interface ClientWorkbenchResponse {
  entity_name: string;
  industry?: string | null;
  naics?: string | null;
  vertical?: string | null;
  revenue_band?: string | null;
  country?: string | null;
  locations?: string | null;
  employees?: string | null;
  domain?: string | null;
  first_seen?: string | null;
  last_seen?: string | null;
  broker?: string | null;
  engagement?: number | null;
  engagement_label?: string | null;
  last_message?: string | null;
  avg_response_hours?: number | null;
  open_queries: number;
  next_renewal_days?: number | null;
  total_premium: number;
  avg_score?: number | null;
  coverages: ClientWorkbenchCoverage[];
  loss_events: ClientWorkbenchLossEvent[];
  threads: ClientWorkbenchThread[];
}
