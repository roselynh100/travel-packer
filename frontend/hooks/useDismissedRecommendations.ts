import { useCallback, useEffect, useState } from "react";

/**
 * Tracks which packing recommendations have been "accepted"
 * (user pressed the primary button in PackingRecommendationModal)
 * so we hide the recommendation status.
 * Resets when tripId changes.
 */
export function useDismissedRecommendations(tripId: string | null) {
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    setDismissedIds(new Set());
  }, [tripId]);

  const isDismissed = useCallback(
    (itemId: string) => dismissedIds.has(itemId),
    [dismissedIds],
  );

  const dismiss = useCallback((itemId: string) => {
    setDismissedIds((prev) => new Set([...prev, itemId]));
  }, []);

  return { isDismissed, dismiss };
}
