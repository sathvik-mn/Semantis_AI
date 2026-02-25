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

export interface HealthStatus {
  status: string;
  service?: string;
  version?: string;
  cache?: { tenants: number; total_entries: number };
  redis?: { status: string };
  system?: { memory_percent: number; memory_available_gb: number; cpu_percent: number };
}

export async function checkHealth(): Promise<HealthStatus> {
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

/** Stream chat completion. Yields content deltas. */
export async function* sendChatCompletionStream(
  request: Omit<ChatRequest, 'stream'> & { stream?: true }
): AsyncGenerator<string, void, unknown> {
  const res = await fetch(`${BACKEND_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: getCacheHeaders(),
    body: JSON.stringify({ ...request, stream: true }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || `HTTP error! status: ${res.status}`);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        try {
          const parsed = JSON.parse(data);
          const content = parsed?.choices?.[0]?.delta?.content;
          if (content) yield content;
        } catch {
          /* skip invalid */
        }
      }
    }
  }
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

// ---------- Organization endpoints ----------

export interface Org {
  id: string;
  name: string;
  slug: string;
  plan: string;
  role: string;
}

export async function getUserOrgs(): Promise<{ orgs: Org[] }> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/orgs`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch organizations');
  return res.json();
}

export async function createOrg(name: string, slug: string): Promise<{ org: Org }> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/orgs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name, slug }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create organization' }));
    throw new Error(err.detail || 'Failed to create organization');
  }
  return res.json();
}

export async function inviteOrgMember(orgId: string, email: string, role: string = 'member'): Promise<{ message: string }> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/orgs/${orgId}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ email, role }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to invite member' }));
    throw new Error(err.detail || 'Failed to invite member');
  }
  return res.json();
}

export async function getAuditLogs(orgId: string, limit: number = 50): Promise<{ audit_logs: any[] }> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/orgs/${orgId}/audit?limit=${limit}`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
}

// ---------- Billing endpoints ----------

export interface BillingPlan {
  name: string;
  price_monthly: number | null;
  max_users: number | null;
  max_requests_month: number | null;
  max_cache_entries: number | null;
}

export interface BillingStatus {
  org_id: string;
  org_name: string;
  plan: string;
  limits: BillingPlan;
  usage_30d: Record<string, number>;
  savings_estimate: {
    cached_requests: number;
    total_requests: number;
    estimated_savings_usd: number;
  };
}

export async function getBillingPlans(): Promise<{ plans: Record<string, BillingPlan>; stripe_enabled: boolean }> {
  const res = await fetch(`${BACKEND_URL}/api/billing/plans`);
  if (!res.ok) throw new Error('Failed to fetch billing plans');
  return res.json();
}

export async function getBillingStatus(): Promise<BillingStatus> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/billing/status`, {
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch billing status');
  return res.json();
}

export interface WarmupEntry {
  prompt: string;
  response: string;
  model?: string;
}

export interface WarmupResult {
  message: string;
  added: number;
  skipped: number;
  errors: number;
}

export async function warmupCache(entries: WarmupEntry[], skipDuplicates = true): Promise<WarmupResult> {
  const token = await getSupabaseToken();
  const res = await fetch(`${BACKEND_URL}/api/cache/warmup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ entries, skip_duplicates: skipDuplicates }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to warm cache' }));
    throw new Error(err.detail || 'Failed to warm cache');
  }
  return res.json();
}

export async function upgradePlan(
  plan: string,
  successUrl?: string,
  cancelUrl?: string
): Promise<{ message: string; redirect_url: string | null }> {
  const token = await getSupabaseToken();
  const base = typeof window !== 'undefined' ? window.location.origin : '';
  const res = await fetch(`${BACKEND_URL}/api/billing/upgrade`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      plan,
      success_url: successUrl || `${base}/settings?billing=success`,
      cancel_url: cancelUrl || `${base}/settings?billing=cancel`,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to upgrade plan' }));
    throw new Error(err.detail || 'Failed to upgrade plan');
  }
  return res.json();
}
