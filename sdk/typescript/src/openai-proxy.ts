/**
 * OpenAI Proxy - Drop-in replacement for OpenAI SDK
 */

import { SemanticCache, ChatCompletionRequest, ChatCompletionResponse } from './index';

export class ChatCompletion {
  private cache: SemanticCache;

  constructor(apiKey: string, baseUrl?: string) {
    this.cache = new SemanticCache({ apiKey, baseUrl });
  }

  /**
   * Create a chat completion (drop-in replacement for OpenAI)
   */
  static async create(
    request: ChatCompletionRequest,
    apiKey: string,
    baseUrl?: string
  ): Promise<ChatCompletionResponse> {
    const cache = new SemanticCache({ apiKey, baseUrl });
    return cache.chat.completions.create(request);
  }
}

export default ChatCompletion;

