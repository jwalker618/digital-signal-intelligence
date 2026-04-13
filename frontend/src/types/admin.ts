// FE: Admin types -- mirrors the B-1..B-4 API contract.

export type HealthStatus = "green" | "amber" | "red";

export interface SystemHealth {
  status: HealthStatus;
  components: Record<string, { status: HealthStatus; detail?: string }>;
  checked_at: string;
}

export interface ExtractorHealth {
  name: string;
  mode: string;
  success_count: number;
  error_count: number;
  last_success_at: string | null;
  last_error_at: string | null;
  last_error: string | null;
  status: HealthStatus;
}

export interface PipelineMetrics {
  total_assessments: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  failure_rate: number;
  window_hours: number;
}

export interface ConfigVersionRow {
  id: string;
  coverage: string;
  config_name: string;
  version: number;
  status: "DRAFT" | "VALIDATING" | "CALIBRATING" | "READY" | "DEPLOYED" | "SUPERSEDED" | "ARCHIVED";
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
