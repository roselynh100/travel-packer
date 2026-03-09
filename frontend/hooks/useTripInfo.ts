import { useCallback, useEffect, useState } from "react";

import { Trip } from "@/constants/types";
import { apiFetch } from "@/constants/api";

type UseTripInfoResult = {
  tripInfo: Trip | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
};

/**
 * useTripInfo
 * Fetches the Trip from GET /trips/{tripId}
 */
export function useTripInfo(tripId: string | null): UseTripInfoResult {
  const [tripInfo, setTripInfo] = useState<Trip | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  /**
   * fetchTripInfo
   * Used when:
   * - tripId changes
   * - packing/unpacking items (bag totals change)
   */
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
      console.log("Fetched trip info:", result);
    } catch (err) {
      console.error("Error fetching trip info:", err);
      setError(err instanceof Error ? err : new Error("Failed to fetch trip"));
    } finally {
      setIsLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    // No active trip -> clear any previous info
    if (!tripId) {
      setTripInfo(null);
      return;
    }

    // tripId changed -> clear stale data and fetch the new trip
    setTripInfo(null);
    void fetchTripInfo();
  }, [tripId, fetchTripInfo]);

  return { tripInfo, isLoading, error, refetch: fetchTripInfo };
}
