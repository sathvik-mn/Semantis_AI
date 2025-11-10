/**
 * Semantis Cache - TypeScript SDK
 * 
 * Easy-to-use SDK for semantic caching in LLM applications.
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

export interface SemanticCacheOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

export interface QueryResponse {
  answer: string;
  meta: {
    hit: 'exact' | 'semantic' | 'miss';
    similarity: number;
    latency_ms: number;
  };
  metrics?: any;
}

export interface ChatCompletionRequest {
  model: string;
  messages: Array<{
    role: string;
    content: string;
  }>;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage?: any;
  meta: {
    hit: 'exact' | 'semantic' | 'miss';
    similarity: number;
    latency_ms: number;
  };
}

export class SemanticCache {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(options: SemanticCacheOptions) {
    this.apiKey = options.apiKey;
    const baseURL = options.baseUrl || 'https://api.semantis.ai';
    
    this.client = axios.create({
      baseURL,
      timeout: options.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Simple query method - returns answer with cache metadata
   */
  async query(prompt: string, model: string = 'gpt-4o-mini'): Promise<QueryResponse> {
    const response = await this.client.get('/query', {
      params: { prompt, model },
    });
    return response.data;
  }

  /**
   * Chat completions (OpenAI-compatible)
   */
  async chatCompletionsCreate(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const response = await this.client.post('/v1/chat/completions', request);
    return response.data;
  }

  /**
   * Get cache metrics
   */
  async getMetrics(): Promise<any> {
    const response = await this.client.get('/metrics');
    return response.data;
  }

  /**
   * OpenAI-compatible interface
   */
  chat = {
    completions: {
      create: (request: ChatCompletionRequest) => this.chatCompletionsCreate(request),
    },
  };
}

// Export for convenience
export default SemanticCache;

