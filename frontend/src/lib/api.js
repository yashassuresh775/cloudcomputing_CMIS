/**
 * External Service API client.
 * Set VITE_API_BASE in .env (e.g. https://xxx.execute-api.region.amazonaws.com)
 * or use /api when proxying in dev.
 */
const BASE = import.meta.env.VITE_API_BASE || '/api';

export async function signup({ email, password, formerStudent, classYear }) {
  const res = await fetch(`${BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      formerStudent: !!formerStudent,
      classYear: classYear || undefined,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ? `${data.error || 'Registration failed'}: ${data.detail}` : (data.error || 'Registration failed'));
  return data;
}

export async function signin({ email, password }) {
  const res = await fetch(`${BASE}/auth/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Sign in failed');
  return data;
}

export async function me(accessToken) {
  const res = await fetch(`${BASE}/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Failed to load profile');
  return data;
}

export async function graduationHandover(accessToken, { uin, classYear }) {
  const res = await fetch(`${BASE}/graduation-handover`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ uin: String(uin).trim(), classYear: classYear || undefined }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ? `${data.error || 'Handover failed'}: ${data.detail}` : (data.error || 'Handover failed'));
  return data;
}
