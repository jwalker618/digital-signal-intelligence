// V6 Phase 44 (C5a) — single-assessment load profile.
// Target: p95 < 5s at 50 RPS, p99 < 10s.
// Run via: k6 run --vus 50 --duration 5m scenarios/single_assessment.js
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.DSI_BASE_URL || 'https://staging.dsi.internal';
const TOKEN = __ENV.DSI_SMOKE_TOKEN || '';

export const options = {
  scenarios: {
    steady_state: {
      executor: 'constant-arrival-rate',
      rate: 50,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 100,
      maxVUs: 200,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<5000', 'p(99)<10000'],
    http_req_failed: ['rate<0.005'],
  },
};

const payload = JSON.stringify({
  coverage: 'cyber',
  entity_name: 'k6-load-target',
  submission_data: {
    revenue: 100000000,
    limit: 5000000,
    deductible: 50000,
    product_type: 'standard',
    industry_sector: 'TECHNOLOGY',
    domain: 'k6-load.example.com',
  },
});

export default function () {
  const r = http.post(`${BASE_URL}/api/v1/assess`, payload, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${TOKEN}`,
    },
    tags: { scenario: 'single_assessment' },
  });
  check(r, {
    'status 200': (r) => r.status === 200,
    'has decision': (r) => r.json('decision') !== undefined,
  });
  sleep(0.1);
}
