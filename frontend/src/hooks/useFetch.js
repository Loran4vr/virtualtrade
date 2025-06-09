import { useState, useEffect, useCallback } from 'react';

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

const cache = new Map();

export function useFetch(url, options = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);

  const fetchData = useCallback(async () => {
    try {
      // Check cache first
      const cachedData = cache.get(url);
      if (cachedData && Date.now() - cachedData.timestamp < CACHE_DURATION) {
        setData(cachedData.data);
        setLoading(false);
        return;
      }

      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();

      // Cache the result
      cache.set(url, {
        data: result,
        timestamp: Date.now()
      });

      setData(result);
      setError(null);
      setRetryCount(0);
    } catch (err) {
      setError(err);
      if (retryCount < MAX_RETRIES) {
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
        }, RETRY_DELAY * Math.pow(2, retryCount)); // Exponential backoff
      }
    } finally {
      setLoading(false);
    }
  }, [url, options, retryCount]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    setLoading(true);
    setRetryCount(0);
    fetchData();
  }, [fetchData]);

  return { data, error, loading, refetch };
} 