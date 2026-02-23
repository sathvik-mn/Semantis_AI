import { supabase } from '../lib/supabase';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// ---------- Types ----------

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  metadata?: Record<string, unknown>;
}

export interface ChatResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  meta: {
    hit: 'exact' | 'semantic' | 'miss';
    similarity: number;
    latency_ms: number;
    strategy: string;
    cache_key?: string;
  };
}

export interface Metrics {
  hit_ratio: number;
  semantic_hit_ratio: number;
  total_requests: number;
  avg_latency_ms: number;
  tokens_saved_est: number;
}

export interface Event {
  timestamp: string;
  tenant_id: string;
  prompt_hash: string;
  decision: string;
  similarity: number;
  latency_ms: number;
}

export interface GenerateApiKeyResponse {
  api_key: string;
  tenant_id: string;
  plan: string;
  created_at: string;
  format: string;
  message: string;
}

export interface GenerateApiKeyParams {
  tenant?: string;
  length?: number;
  plan?: string;
}

export interface CurrentApiKeyResponse {
  api_key?: string;
  tenant_id?: string;
  plan?: string;
  created_at?: string;
  exists: boolean;
  message?: string;
}

export interface OpenAIKeyStatus {
  key_set: boolean;
  key_preview?: string;
  message?: string;
}

// ---------- API Key helpers ----------

export function getApiKey(): string | null {
  return localStorage.getItem('semantic_api_key');
}

export function setApiKey(key: string): void {
  localStorage.setItem('semantic_api_key', key);
}

export function clearApiKey(): void {
  localStorage.removeItem('semantic_api_key');
}

export function hasApiKey(): boolean {
  return !!getApiKey();
}

// ---------- Auth header helpers ----------

async function getSupabaseToken(): Promise<string> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error('Authentication required. Please log in first.');
  }
  return session.access_token;
}

function getCacheHeaders(): HeadersInit {
  const apiKey = getApiKey();
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;
  return headers;
}

// ---------- Public API ----------

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BACKEND_URL}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function sendChatCompletion(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${BACKEND_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: getCacheHeaders(),
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP error! status: ${res.status}`);
  }
  return res.json();
}

export async function getMetrics(): Promise<Metrics> {
  const res = await fetch(`${BACKEND_URL}/metrics`, { headers: getCacheHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.status}`);
  return res.json();
}

export async function getEvents(limit: number = 100): Promise<Event[]> {
  const res = await fetch(`${BACKEND_URL}/events?limit=${limit}`, { headers: getCacheHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.status}`);
  return res.json();
}

// ---------- Settings endpoints ----------

export async function getSettings(): Promise<{ sim_threshold: number; ttl_days: number; entries: number }> {
  const res = await fetch(`${BACKEND_URL}/settings`, { headers: getCacheHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch settings: ${res.status}`);
  return res.json();
}

export async function updateSettings(settings: { sim_threshold?: number; ttl_days?: number }): Promise<{ status: string; settings: Record<string, number> }> {
  const res = await fetch(`${BACKEND_URL}/settings`, {
    method: 'PUT',
    headers: getCacheHeaders(),
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error(`Failed to update settings: ${res.status}`);
  return res.json();
}

// ---------- Authenticated endpoints (use Supabase token) ----------

export async function getCurrentApiKey(): Promise<CurrentApiKeyResponse> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/keys/current`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to get API key' }));
    throw new Error(err.detail || 'Failed to get API key');
  }
  return res.json();
}

export async function generateApiKey(params: GenerateApiKeyParams = {}): Promise<GenerateApiKeyResponse> {
  const token = await getSupabaseToken();
  const qp = new URLSearchParams();
  if (params.tenant) qp.append('tenant', params.tenant);
  if (params.length) qp.append('length', params.length.toString());
  if (params.plan) qp.append('plan', params.plan);

  const res = await fetch(`${BACKEND_URL}/api/keys/generate?${qp.toString()}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to generate API key' }));
    throw new Error(err.detail || 'Failed to generate API key');
  }
  return res.json();
}

export async function getUserOpenAIKeyStatus(): Promise<OpenAIKeyStatus> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/users/openai-key`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to get OpenAI key status' }));
    throw new Error(err.detail || 'Failed to get OpenAI key status');
  }
  return res.json();
}

export async function setUserOpenAIKey(apiKey: string): Promise<{ message: string; key_set: boolean }> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/users/openai-key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ api_key: apiKey }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to set OpenAI key' }));
    throw new Error(err.detail || 'Failed to set OpenAI key');
  }
  return res.json();
}

export async function removeUserOpenAIKey(): Promise<{ message: string; key_set: boolean }> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/users/openai-key`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to remove OpenAI key' }));
    throw new Error(err.detail || 'Failed to remove OpenAI key');
  }
  return res.json();
}
