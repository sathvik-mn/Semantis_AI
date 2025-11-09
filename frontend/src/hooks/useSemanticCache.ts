import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/semanticAPI';

export function useSemanticCache() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendQuery = useCallback(async (request: api.ChatRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.sendChatCompletion(request);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { sendQuery, isLoading, error };
}

export function useMetrics(refreshInterval?: number) {
  const [metrics, setMetrics] = useState<api.Metrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    if (!api.hasApiKey()) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await api.getMetrics();
      setMetrics(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch metrics';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();

    if (refreshInterval) {
      const interval = setInterval(fetchMetrics, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchMetrics, refreshInterval]);

  return { metrics, isLoading, error, refetch: fetchMetrics };
}

export function useEvents(limit: number = 100, refreshInterval?: number) {
  const [events, setEvents] = useState<api.Event[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    if (!api.hasApiKey()) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await api.getEvents(limit);
      setEvents(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch events';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchEvents();

    if (refreshInterval) {
      const interval = setInterval(fetchEvents, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchEvents, refreshInterval]);

  return { events, isLoading, error, refetch: fetchEvents };
}

export function useHealthCheck(intervalMs: number = 30000) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      await api.checkHealth();
      setIsHealthy(true);
    } catch {
      setIsHealthy(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, intervalMs);
    return () => clearInterval(interval);
  }, [checkHealth, intervalMs]);

  return isHealthy;
}
