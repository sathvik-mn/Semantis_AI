const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

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

export function getApiKey(): string | null {
  return localStorage.getItem('semantic_api_key');
}

function getHeaders(): HeadersInit {
  const apiKey = getApiKey();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (apiKey) {
    headers['Authorization'] = `Bearer ${apiKey}`;
  }

  return headers;
}

export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetch(`${BACKEND_URL}/health`);
  if (!response.ok) {
    throw new Error('Backend health check failed');
  }
  return response.json();
}

export async function sendChatCompletion(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${BACKEND_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function getMetrics(): Promise<Metrics> {
  const response = await fetch(`${BACKEND_URL}/metrics`, {
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch metrics: ${response.status}`);
  }

  return response.json();
}

export async function getEvents(limit: number = 100): Promise<Event[]> {
  const response = await fetch(`${BACKEND_URL}/events?limit=${limit}`, {
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch events: ${response.status}`);
  }

  return response.json();
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
  email?: string;
  name?: string;
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

export async function getCurrentApiKey(): Promise<CurrentApiKeyResponse> {
  // Get auth token from localStorage
  const authToken = localStorage.getItem('auth_token');
  if (!authToken) {
    throw new Error('Authentication required. Please log in first.');
  }

  const response = await fetch(`${BACKEND_URL}/api/keys/current`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get API key' }));
    throw new Error(error.detail || 'Failed to get API key');
  }

  return response.json();
}

export interface OpenAIKeyStatus {
  key_set: boolean;
  key_preview?: string;
  message?: string;
}

export async function getUserOpenAIKeyStatus(): Promise<OpenAIKeyStatus> {
  const authToken = localStorage.getItem('auth_token');
  if (!authToken) {
    throw new Error('Authentication required. Please log in first.');
  }

  const response = await fetch(`${BACKEND_URL}/api/users/openai-key`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get OpenAI key status' }));
    throw new Error(error.detail || 'Failed to get OpenAI key status');
  }

  return response.json();
}

export async function setUserOpenAIKey(apiKey: string): Promise<{ message: string; key_set: boolean }> {
  const authToken = localStorage.getItem('auth_token');
  if (!authToken) {
    throw new Error('Authentication required. Please log in first.');
  }

  const response = await fetch(`${BACKEND_URL}/api/users/openai-key`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
    body: JSON.stringify({ api_key: apiKey }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to set OpenAI key' }));
    throw new Error(error.detail || 'Failed to set OpenAI key');
  }

  return response.json();
}

export async function removeUserOpenAIKey(): Promise<{ message: string; key_set: boolean }> {
  const authToken = localStorage.getItem('auth_token');
  if (!authToken) {
    throw new Error('Authentication required. Please log in first.');
  }

  const response = await fetch(`${BACKEND_URL}/api/users/openai-key`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to remove OpenAI key' }));
    throw new Error(error.detail || 'Failed to remove OpenAI key');
  }

  return response.json();
}

export async function generateApiKey(params: GenerateApiKeyParams = {}): Promise<GenerateApiKeyResponse> {
  const queryParams = new URLSearchParams();
  if (params.tenant) queryParams.append('tenant', params.tenant);
  if (params.length) queryParams.append('length', params.length.toString());
  if (params.plan) queryParams.append('plan', params.plan);

  // Get auth token from localStorage
  const authToken = localStorage.getItem('auth_token');
  if (!authToken) {
    throw new Error('Authentication required. Please log in first.');
  }

  const response = await fetch(`${BACKEND_URL}/api/keys/generate?${queryParams.toString()}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to generate API key' }));
    throw new Error(error.detail || 'Failed to generate API key');
  }

  return response.json();
}