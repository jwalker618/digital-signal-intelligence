// v8 Phase 8 — portal API client.
//
// Typed fetch helpers for the 8 endpoints under /api/v1/portal/*.
// Uses the existing authorizedFetch from authApi for token injection;
// each helper expects the caller to pass the current access token
// (typically `useAuthStore.getState().accessToken`).

import { authorizedFetch } from "@/lib/authApi";
import type {
  ActionsResponse,
  BrokerQueriesResponse,
  BrokerRecommendationsResponse,
  BrokerReplyRequest,
  BrokerReplyResponse,
  ClientProfileResponse,
  CommunicationsListResponse,
  CommunicationsThreadResponse,
  CoverageRequestPayload,
  CoverageRequestResponse,
  OverviewResponse,
  PeersResponse,
  ScoreResponse,
  SendRecommendationPayload,
  SendRecommendationResponse,
  SubmissionDetailResponse,
} from "@/types/portal";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function url(path: string): string {
  return `${API_BASE}${path}`;
}

async function getJson<T>(token: string | null, path: string): Promise<T> {
  const res = await authorizedFetch(token, url(`/api/v1/portal${path}`));
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Portal GET ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

async function postJson<TResp, TReq>(
  token: string | null, path: string, body: TReq,
): Promise<TResp> {
  const res = await authorizedFetch(token, url(`/api/v1/portal${path}`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Portal POST ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<TResp>;
}

// ----------------------------------------------------------------------------
// GET endpoints
// ----------------------------------------------------------------------------

export function fetchOverview(token: string | null): Promise<OverviewResponse> {
  return getJson<OverviewResponse>(token, "/overview");
}

export function fetchSubmissionDetail(
  token: string | null, submissionCode: string,
): Promise<SubmissionDetailResponse> {
  return getJson<SubmissionDetailResponse>(
    token, `/submissions/${encodeURIComponent(submissionCode)}`,
  );
}

export function fetchSubmissionScore(
  token: string | null, submissionCode: string,
): Promise<ScoreResponse> {
  return getJson<ScoreResponse>(
    token, `/submissions/${encodeURIComponent(submissionCode)}/score`,
  );
}

export function fetchSubmissionPeers(
  token: string | null, submissionCode: string,
): Promise<PeersResponse> {
  return getJson<PeersResponse>(
    token, `/submissions/${encodeURIComponent(submissionCode)}/peers`,
  );
}

export function fetchSubmissionActions(
  token: string | null, submissionCode: string,
): Promise<ActionsResponse> {
  return getJson<ActionsResponse>(
    token, `/submissions/${encodeURIComponent(submissionCode)}/actions`,
  );
}

export function fetchBrokerQueries(token: string | null): Promise<BrokerQueriesResponse> {
  return getJson<BrokerQueriesResponse>(token, "/queries");
}

// ----------------------------------------------------------------------------
// Reply (POST)
// ----------------------------------------------------------------------------

export function postBrokerReply(
  token: string | null,
  referralCode: string,
  payload: BrokerReplyRequest,
): Promise<BrokerReplyResponse> {
  return postJson<BrokerReplyResponse, BrokerReplyRequest>(
    token, `/queries/${encodeURIComponent(referralCode)}/reply`, payload,
  );
}

export function fetchCommunications(
  token: string | null, openOnly = false,
): Promise<CommunicationsListResponse> {
  return getJson<CommunicationsListResponse>(
    token, `/communications${openOnly ? "?open_only=true" : ""}`,
  );
}

export function fetchCommunicationThread(
  token: string | null, referralCode: string,
): Promise<CommunicationsThreadResponse> {
  return getJson<CommunicationsThreadResponse>(
    token, `/communications/${encodeURIComponent(referralCode)}`,
  );
}

// ----------------------------------------------------------------------------
// v8.1: profile, coverage requests, broker recommendations
// ----------------------------------------------------------------------------

export function fetchClientProfile(token: string | null): Promise<ClientProfileResponse> {
  return getJson<ClientProfileResponse>(token, "/profile");
}

export function postCoverageRequest(
  token: string | null, payload: CoverageRequestPayload,
): Promise<CoverageRequestResponse> {
  return postJson<CoverageRequestResponse, CoverageRequestPayload>(
    token, "/coverage-requests", payload,
  );
}

export function fetchBrokerRecommendations(
  token: string | null,
): Promise<BrokerRecommendationsResponse> {
  return getJson<BrokerRecommendationsResponse>(token, "/recommendations");
}

export function postSendRecommendation(
  token: string | null, payload: SendRecommendationPayload,
): Promise<SendRecommendationResponse> {
  return postJson<SendRecommendationResponse, SendRecommendationPayload>(
    token, "/recommendations/send", payload,
  );
}
