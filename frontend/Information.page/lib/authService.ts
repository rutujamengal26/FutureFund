import { fetchAPI } from './api';

export async function login(email: string, password: string) {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);

  const response = await fetchAPI('/api/v1/auth/login', {
    method: 'POST',
    body: params,
  });

  if (response.access_token) {
    localStorage.setItem('token', response.access_token);
  }
  return response;
}

export async function register(email: string, password: string) {
  const response = await fetchAPI('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name: "User" }), // Some backends need full_name, wait, UserCreate only has email/password? Let's check schemas/user.py.
  });
  return response;
}

export function logout() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
  }
}

export function isAuthenticated() {
  return typeof window !== 'undefined' ? !!localStorage.getItem('token') : false;
}
