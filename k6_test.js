import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m', target: 50 },
    { duration: '10s', target: 0 },
  ],
};

const BASE = 'http://localhost:8080';

export function setup() {
  const res = http.post(
    BASE + '/v1/auth/login',
    JSON.stringify({ email: 'admin@smartretailx.com', password: 'Admin123!' }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  return { token: res.json('access_token') };
}

export default function (data) {
  const headers = {
    Authorization: 'Bearer ' + data.token,
    'Content-Type': 'application/json'
  };

  check(http.get(BASE + '/v1/products', { headers }), {
    'products 200': function (r) { return r.status === 200; }
  });
  sleep(0.5);
  check(http.get(BASE + '/v1/inventory', { headers }), {
    'inventory 200': function (r) { return r.status === 200; }
  });
  sleep(0.5);
}