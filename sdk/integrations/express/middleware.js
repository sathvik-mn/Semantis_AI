/**
 * Express.js Middleware for Semantis Cache
 * 
 * Automatically caches OpenAI API calls in Express applications.
 */

const { SemanticCache } = require('semantis-cache');

/**
 * Create semantic cache middleware for Express
 * 
 * @param {Object} options - Middleware options
 * @param {string} options.apiKey - Semantis AI API key
 * @param {string} [options.baseUrl] - API base URL (default: https://api.semantis.ai)
 * @param {string[]} [options.cachePaths] - Paths to cache (default: ["/v1/chat/completions"])
 * @returns {Function} Express middleware function
 * 
 * @example
 * const express = require('express');
 * const semanticCacheMiddleware = require('semantis-cache/integrations/express');
 * 
 * const app = express();
 * app.use(express.json());
 * 
 * // Add middleware
 * app.use(semanticCacheMiddleware({
 *   apiKey: 'sc-your-key',
 *   cachePaths: ['/v1/chat/completions']
 * }));
 */
function semanticCacheMiddleware(options) {
  const {
    apiKey,
    baseUrl = process.env.SEMANTIS_API_URL || 'https://api.semantis.ai',
    cachePaths = ['/v1/chat/completions'],
  } = options;

  if (!apiKey) {
    throw new Error('API key is required. Provide it in options or set SEMANTIS_API_KEY environment variable.');
  }

  // Initialize cache client
  const cache = new SemanticCache({
    apiKey: apiKey || process.env.SEMANTIS_API_KEY,
    baseUrl: baseUrl,
  });

  return async (req, res, next) => {
    // Check if this path should be cached
    if (!cachePaths.includes(req.path)) {
      return next();
    }

    // Only cache POST requests (OpenAI API calls)
    if (req.method !== 'POST') {
      return next();
    }

    try {
      // Extract prompt from request body
      const messages = req.body.messages || [];
      if (messages.length === 0) {
        return next();
      }

      // Get the last user message
      const userMessages = messages.filter(msg => msg.role === 'user');
      if (userMessages.length === 0) {
        return next();
      }

      const prompt = userMessages[userMessages.length - 1].content;
      if (!prompt) {
        return next();
      }

      // Check cache
      try {
        const response = await cache.query(prompt, req.body.model || 'gpt-4o-mini');

        // If cache hit, return cached response
        if (response.cacheHit === 'exact' || response.cacheHit === 'semantic') {
          // Format as OpenAI response
          const cachedResponse = {
            id: `chatcmpl-cached-${hashCode(prompt)}`,
            object: 'chat.completion',
            created: Math.floor(Date.now() / 1000),
            model: req.body.model || 'gpt-4o-mini',
            choices: [{
              index: 0,
              message: {
                role: 'assistant',
                content: response.answer,
              },
              finish_reason: 'stop',
            }],
            usage: {
              prompt_tokens: 0,
              completion_tokens: 0,
              total_tokens: 0,
            },
            meta: {
              hit: response.cacheHit,
              similarity: response.similarity,
              latency_ms: response.latencyMs,
            },
          };

          return res.json(cachedResponse);
        }
      } catch (error) {
        // If cache fails, continue to original endpoint
        console.warn('Cache error:', error.message);
      }
    } catch (error) {
      // If anything fails, continue to original endpoint
      console.warn('Middleware error:', error.message);
    }

    // If no cache hit, continue to original endpoint
    next();
  };
}

/**
 * Simple hash function for prompt
 */
function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(36);
}

module.exports = semanticCacheMiddleware;

