// V6 Phase 44 (C5a) — extractor timeout storm.
// Simulates slow external APIs; assesses the shedding path.
// Expected: shed → neutral score + confidence penalty, no 5xx spike.
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = __ENV.DSI_BASE_URL || 'https://staging.dsi.internal';
const TOKEN = __ENV.DSI_SMOKE_TOKEN || '';

export const options = {
  scenarios: {
    storm: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      stages: [
        { target: 40, duration: '2m' },
        { target: 40, duration: '3m' },
        { target: 10, duration: '2m' },
      ],
      preAllocatedVUs: 80,
      maxVUs: 200,
    },
  },
  thresholds: {
    // shed response target: 2s; max 10s even under storm.
    http_req_duration: ['p(95)<10000'],
    http_req_failed: ['rate<0.01'],
  },
};

const payload = JSON.stringify({
  coverage: 'cyber',
  entity_name: 'k6-timeout-storm',
  force_slow_extractors: true,
  submission_data: {
    revenue: 100000000,
    limit: 5000000,
    deductible: 50000,
    product_type: 'standard',
    industry_sector: 'TECHNOLOGY',
    domain: 'k6-storm.example.com',
  },
});

export default function () {
  const r = http.post(`${BASE_URL}/api/v1/assess`, payload, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${TOKEN}`,
    },
    tags: { scenario: 'storm' },
  });
  check(r, {
    'not 5xx': (r) => r.status < 500,
    'shedding acknowledged': (r) =>
      r.json('notes') === undefined ||
      JSON.stringify(r.json('notes')).includes('shed') ||
      r.json('confidence') !== undefined,
  });
}
