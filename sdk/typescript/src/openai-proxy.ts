/**
 * OpenAI Proxy — drop-in replacement for the OpenAI SDK.
 *
 * Usage:
 *   import { SemantisOpenAI } from 'semantis-cache/openai-proxy';
 *   const client = new SemantisOpenAI({ apiKey: 'sc-...' });
 *   const resp = await client.chat.completions.create({ ... });
 */

import {
  SemanticCache,
  ChatCompletionRequest,
  ChatCompletionResponse,
  SemanticCacheOptions,
} from './index';

export class SemantisOpenAI {
  private cache: SemanticCache;
  chat: { completions: { create: (req: ChatCompletionRequest) => Promise<ChatCompletionResponse> } };

  constructor(options: SemanticCacheOptions) {
    this.cache = new SemanticCache(options);
    this.chat = {
      completions: {
        create: (request: ChatCompletionRequest) =>
          this.cache.chatCompletionsCreate(request),
      },
    };
  }
}

export default SemantisOpenAI;
