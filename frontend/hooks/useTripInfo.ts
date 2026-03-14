import { useCallback, useEffect, useState } from "react";

import { Trip } from "@/constants/types";
import { apiFetch } from "@/constants/api";

type UseTripInfoResult = {
  tripInfo: Trip | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  refreshTotals: () => Promise<void>;
};

/**
 * useTripInfo
 * Fetches the Trip from GET /trips/{tripId}. If weather is missing, GET /trips/{tripId}/weather.
 */
export function useTripInfo(tripId: string | null): UseTripInfoResult {
  const [tripInfo, setTripInfo] = useState<Trip | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchTripInfo = useCallback(async () => {
    if (!tripId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiFetch(`/trips/${tripId}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API error (${response.status}): ${errorText || response.statusText}`,
        );
      }

      const result: Trip = await response.json();
      setTripInfo(result);

      const needsWeather =
        result.lowest_temp == null && result.highest_temp == null;
      if (needsWeather) {
        const weatherRes = await apiFetch(`/trips/${tripId}/weather`);
        if (weatherRes.ok) {
          const withWeather: Trip = await weatherRes.json();
          setTripInfo(withWeather);
        }
      }
    } catch (err) {
      console.error("Error fetching trip info:", err);
      setError(err instanceof Error ? err : new Error("Failed to fetch trip"));
    } finally {
      setIsLoading(false);
    }
  }, [tripId]);

  /**
   * After pack/unpack: POST recalculate-totals
   * Then merge new totals into tripInfo so pills update
   */
  const refreshTotals = useCallback(async () => {
    if (!tripId) return;

    try {
      const response = await apiFetch(`/trips/${tripId}/recalculate-totals`, {
        method: "POST",
      });
      if (!response.ok) return;

      const data = await response.json();
      setTripInfo((prev) =>
        prev
          ? {
              ...prev,
              total_items_weight: data.total_weight,
              total_items_volume: data.total_volume,
            }
          : null,
      );
    } catch (err) {
      console.error("refreshTotals failed:", err);
    }
  }, [tripId]);

  // tripId changed -> clear stale data and fetch the new trip
  useEffect(() => {
    setTripInfo(null);
    void fetchTripInfo();
  }, [tripId, fetchTripInfo]);

  return {
    tripInfo,
    isLoading,
    error,
    refetch: fetchTripInfo,
    refreshTotals,
  };
}
