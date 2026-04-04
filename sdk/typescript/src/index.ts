/**
 * Semantys Cache - TypeScript SDK
 *
 * Drop-in semantic caching layer for LLM applications.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// ── Types ──

export interface SemanticCacheOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

export interface CacheMeta {
  hit: 'exact' | 'semantic' | 'miss' | 'fallback';
  similarity: number;
  latency_ms: number;
  strategy?: string;
}

export interface QueryResponse {
  answer: string;
  meta: CacheMeta;
  metrics?: Record<string, unknown>;
}

export interface ChatMessage {
  role: string;
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  ttl_seconds?: number;
  stream?: boolean;
}

export interface ChatCompletionChoice {
  index: number;
  message: ChatMessage;
  finish_reason: string;
}

export interface ChatCompletionUsage {
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: ChatCompletionChoice[];
  usage?: ChatCompletionUsage;
  meta: CacheMeta;
}

export interface HealthResponse {
  status: string;
  [key: string]: unknown;
}

export interface MetricsResponse {
  [key: string]: unknown;
}

// ── Error class ──

export class SemantysError extends Error {
  status?: number;
  code?: string;

  constructor(message: string, status?: number, code?: string) {
    super(message);
    this.name = 'SemantysError';
    this.status = status;
    this.code = code;
  }
}

// ── Client ──

export class SemanticCache {
  private client: AxiosInstance;
  private apiKey: string;
  private maxRetries: number;

  constructor(options: SemanticCacheOptions) {
    if (!options.apiKey) {
      throw new SemantysError('apiKey is required');
    }
    this.apiKey = options.apiKey;
    this.maxRetries = options.maxRetries ?? 3;
    const baseURL = (options.baseUrl || 'https://api.semantys.ai').replace(/\/+$/, '');

    this.client = axios.create({
      baseURL,
      timeout: options.timeout || 30000,
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': 'semantys-typescript/1.0.0',
      },
    });
  }

  // ── Internal helpers ──

  private async requestWithRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: unknown;
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        lastError = err;
        if (err instanceof AxiosError) {
          const status = err.response?.status;
          // Retry on 429 (rate-limit) and 5xx (server errors)
          if (status === 429 || (status && status >= 500)) {
            const wait = Math.min(2 ** attempt * 1000, 8000);
            await new Promise((r) => setTimeout(r, wait));
            continue;
          }
        }
        // Non-retryable error — throw immediately
        throw this.wrapError(err);
      }
    }
    throw this.wrapError(lastError);
  }

  private wrapError(err: unknown): SemantysError {
    if (err instanceof SemantysError) return err;
    if (err instanceof AxiosError) {
      const status = err.response?.status;
      const body = err.response?.data as Record<string, unknown> | undefined;
      const message =
        (body?.detail as string) || (body?.error as string) || err.message;
      return new SemantysError(message, status, err.code);
    }
    if (err instanceof Error) return new SemantysError(err.message);
    return new SemantysError(String(err));
  }

  // ── Public API ──

  /** Simple query — returns answer with cache metadata. */
  async query(prompt: string, model: string = 'gpt-4o-mini'): Promise<QueryResponse> {
    return this.requestWithRetry(async () => {
      const resp = await this.client.get<QueryResponse>('/query', {
        params: { prompt, model },
      });
      return resp.data;
    });
  }

  /** OpenAI-compatible chat completions. */
  async chatCompletionsCreate(
    request: ChatCompletionRequest,
  ): Promise<ChatCompletionResponse> {
    return this.requestWithRetry(async () => {
      const resp = await this.client.post<ChatCompletionResponse>(
        '/v1/chat/completions',
        request,
      );
      return resp.data;
    });
  }

  /** Get cache metrics for the authenticated tenant. */
  async getMetrics(): Promise<MetricsResponse> {
    return this.requestWithRetry(async () => {
      const resp = await this.client.get<MetricsResponse>('/metrics');
      return resp.data;
    });
  }

  /** Health check. */
  async health(): Promise<HealthResponse> {
    return this.requestWithRetry(async () => {
      const resp = await this.client.get<HealthResponse>('/health');
      return resp.data;
    });
  }

  /** OpenAI-compatible interface: cache.chat.completions.create(...) */
  chat = {
    completions: {
      create: (request: ChatCompletionRequest) =>
        this.chatCompletionsCreate(request),
    },
  };
}

export default SemanticCache;
