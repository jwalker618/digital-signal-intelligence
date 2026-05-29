// FE: Admin types -- mirrors the B-1..B-4 API contract.

export type HealthStatus = "green" | "amber" | "red";

export interface SubsystemHealth {
  name: string;
  status: HealthStatus;
  detail?: string | null;
  metrics?: Record<string, unknown>;
  latency_ms?: number | null;
}

export interface SystemHealth {
  overall: HealthStatus;
  evaluated_at: string;
  subsystems: SubsystemHealth[];
}

export interface ExtractorHealth {
  extractor_id: string;
  coverage: string;
  signal_type: string;
  success_count_24h: number;
  error_count_24h: number;
  success_rate: number;
  avg_latency_ms: number;
  last_success_at: string | null;
  last_error_at: string | null;
  last_error_message: string | null;
  data_freshness_score: number;
  // Derived/optional status badge (not part of the API payload).
  status?: HealthStatus;
}

export interface PipelineMetrics {
  period: string;
  coverage: string | null;
  captured_at: string;
  assessments_total: number;
  assessments_per_hour: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  avg_latency_ms: number;
  failure_count: number;
  failure_rate: number;
  decision_mix: Record<string, number>;
}

export interface ConfigVersionRow {
  id: string;
  coverage: string;
  config_name: string;
  version_number: number;
  status:
    | "DRAFT"
    | "VALIDATED"
    | "CALIBRATED"
    | "DEPLOYED"
    | "ROLLED_BACK"
    | "SUPERSEDED"
    | "DISK_ONLY";
  notes: string | null;
  author_id: string | null;
  created_at: string;
  updated_at: string;
  has_validation_report: boolean;
  has_calibration_report: boolean;
}

export interface AuditEventRow {
  id: string;
  tenant_id: string | null;
  user_id: string | null;
  request_id: string | null;
  action_type: string;
  resource_type: string | null;
  resource_id: string | null;
  before_state: unknown;
  after_state: unknown;
  details: unknown;
  ip_address: string | null;
  user_agent: string | null;
  duration_ms: number | null;
  created_at: string | null;
}

export interface UserRow {
  id: string;
  email: string;
  full_name: string | null;
  role_id: string | null;
  role_name: string | null;
  is_active: boolean;
  is_locked: boolean;
  mfa_enabled: boolean;
  last_login: string | null;
  created_at: string;
}

export interface RoleRow {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
  is_system: boolean;
  user_count: number;
}

export interface InvitationRow {
  id: string;
  email: string;
  role_id: string | null;
  role_name: string | null;
  inviter_id: string | null;
  expires_at: string;
  accepted_at: string | null;
  cancelled_at: string | null;
  created_at: string;
}
