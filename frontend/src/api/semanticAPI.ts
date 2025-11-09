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

function getApiKey(): string | null {
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
