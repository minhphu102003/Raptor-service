import http from 'k6/http';
import { Trend } from 'k6/metrics';
import { sleep, check } from 'k6';

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const RETRIEVE = `${BASE}/v1/documents/retrieve`;
const HEALTH = `${BASE}/health`;

const payload = JSON.stringify({
  dataset_id: 'ds_demo',
  mode: 'collapsed',
  query: 'What is Marketing Decision Support Systems ?',
});
const headers = { 'Content-Type': 'application/json' };

// custom metric: đọc header lag do middleware chèn
const loopLagMs = new Trend('loop_lag_ms');

export const options = {
  discardResponseBodies: true,
  scenarios: {
    // Đè tải retrieval
    retrieval: { executor: 'constant-vus', vus: 300, duration: '60s', exec: 'hitRetrieve' },
    // Đo /health với RPS cố định (để soi TTFB)
    probe: {
      executor: 'constant-arrival-rate',
      rate: 100, timeUnit: '1s', duration: '60s',
      preAllocatedVUs: 50, maxVUs: 200,
      exec: 'hitHealth'
    },
  },
  thresholds: {
    http_req_waiting: ['p(95)<5000', 'p(99)<8000'],  // TTFB dưới tải
    http_req_failed:  ['rate<0.05'],
    // Nếu event loop bị block, metric này sẽ “đỏ”:
    'loop_lag_ms':    ['p(95)<50', 'p(99)<100'],
  }
};

export function hitRetrieve() {
  const r = http.post(RETRIEVE, payload, { headers, timeout: '30s' });
  const lag = parseFloat(r.headers['X-Event-Loop-Lag-p95-ms'] || '0');
  loopLagMs.add(lag);
  check(r, { 'status ok-ish': resp => resp.status && resp.status < 500 });
  sleep(0.05);
}

export function hitHealth() {
  const r = http.get(HEALTH, { timeout: '10s' });
  const lag = parseFloat(r.headers['X-Event-Loop-Lag-p95-ms'] || '0');
  loopLagMs.add(lag);
  check(r, { 'health 200': resp => resp.status === 200 });
}
