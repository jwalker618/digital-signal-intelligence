// V6 Phase 44 (C5a) — multiplex race profile.
// Target: p95 < 8s at 20 RPS, no cross-config leakage.
// Triggers `/api/v1/assess?multiplex=all` which fans out to every
// candidate config, races, and returns the best.
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.DSI_BASE_URL || 'https://staging.dsi.internal';
const TOKEN = __ENV.DSI_SMOKE_TOKEN || '';

export const options = {
  scenarios: {
    race: {
      executor: 'constant-arrival-rate',
      rate: 20,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 80,
      maxVUs: 200,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<8000'],
    http_req_failed: ['rate<0.01'],
    'checks{scenario:race}': ['rate>0.99'],
  },
};

const payload = JSON.stringify({
  coverage: 'cyber',
  entity_name: 'k6-multiplex-target',
  multiplex: true,
  submission_data: {
    revenue: 500000000,
    limit: 25000000,
    deductible: 250000,
    product_type: 'standard',
    industry_sector: 'FINANCIAL_SERVICES',
    domain: 'k6-multiplex.example.com',
  },
});

export default function () {
  const r = http.post(`${BASE_URL}/api/v1/assess`, payload, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${TOKEN}`,
    },
    tags: { scenario: 'race' },
  });
  check(r, {
    'status 200': (r) => r.status === 200,
    'selected config present': (r) => r.json('config_id') !== undefined,
    'no cross-coverage bleed': (r) => r.json('coverage') === 'cyber',
  }, { scenario: 'race' });
}
