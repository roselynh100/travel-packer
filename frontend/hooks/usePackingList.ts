import { useCallback, useEffect, useState } from "react";

import {
  ItemWithPackingRecommendation,
  RecommendedItem,
} from "@/constants/types";
import { apiFetch } from "@/constants/api";

function removeNRecommendedItemsByName(
  recs: RecommendedItem[],
  itemName: string,
  n: number,
): RecommendedItem[] {
  if (n <= 0) return recs;
  let remaining = n;
  return recs.filter((rec) => {
    if (remaining > 0 && rec.item_name === itemName) {
      remaining -= 1;
      return false;
    }
    return true;
  });
}

/**
 * Pass in a callback to refresh trip totals after packing/unpacking.
 */
type UsePackingListOptions = {
  onTripChanged?: () => Promise<void> | void;
};

type UsePackingListResult = {
  recommendedItems: RecommendedItem[];
  scannedItems: ItemWithPackingRecommendation[];
  checkedItems: Set<string>;
  toggleItem: (id: string) => Promise<void>;
  packItem: (itemId: string) => Promise<void>;
  unpackItem: (itemId: string) => Promise<void>;
  updateItemQuantity: (itemId: string, quantity: number) => Promise<void>;
  setRecommendationAccepted: (
    itemId: string,
    recommendationId: string,
    isAccepted: boolean,
  ) => Promise<void>;
};

/**
 * usePackingList
 * - Fetches initial recommendations from GET /trips/{tripId}/recommendations
 * - Merges in the current scanned item from AppContext
 * - Packs/unpacks items via POST/DELETE /trips/{tripId}/item/{itemId}
 * - Notifies the caller via `onTripChanged` so trip totals can refresh
 */
export function usePackingList(
  tripId: string | null,
  currentItem: ItemWithPackingRecommendation | null,
  options: UsePackingListOptions = {},
): UsePackingListResult {
  const { onTripChanged } = options;

  const [recommendedItems, setRecommendedItems] = useState<RecommendedItem[]>(
    [],
  );
  const [scannedItems, setScannedItems] = useState<
    ItemWithPackingRecommendation[]
  >([]);
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());

  // Initial recommendations fetch whenever tripId changes
  useEffect(() => {
    if (!tripId) return;

    setRecommendedItems([]);
    setScannedItems([]);
    setCheckedItems(new Set());

    const fetchRecommendations = async () => {
      try {
        const response = await apiFetch(`/trips/${tripId}/recommendations`);

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        const result: RecommendedItem[] = await response.json();
        setRecommendedItems(result);
        console.log("Fetched recommendations:", result);
      } catch (error) {
        console.error("Error fetching recommendations:", error);
      }
    };

    void fetchRecommendations();
  }, [tripId]);

  const packItem = useCallback(
    async (itemId: string) => {
      if (!tripId) return;

      try {
        const response = await apiFetch(`/trips/${tripId}/item/${itemId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        setCheckedItems((prev) => new Set([...prev, itemId]));

        if (onTripChanged) {
          await onTripChanged();
        }
      } catch (error) {
        console.error("Error packing item:", error);
        throw error;
      }
    },
    [tripId, onTripChanged],
  );

  const unpackItem = useCallback(
    async (itemId: string) => {
      if (!tripId) return;

      try {
        const response = await apiFetch(`/trips/${tripId}/item/${itemId}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        setCheckedItems(
          (prev) => new Set([...prev].filter((id) => id !== itemId)),
        );

        if (onTripChanged) {
          await onTripChanged();
        }
      } catch (error) {
        console.error("Error unpacking item:", error);
        throw error;
      }
    },
    [tripId, onTripChanged],
  );

  const setRecommendationAccepted = useCallback(
    async (itemId: string, recommendationId: string, isAccepted: boolean) => {
      if (!tripId) return;
      try {
        const response = await apiFetch(
          `/trips/${tripId}/recommendations/${encodeURIComponent(recommendationId)}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_accepted: isAccepted }),
          },
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        // Update local scannedItems so pill hides/shows immediately
        setScannedItems((prev) =>
          prev.map((item) =>
            item.item_id === itemId && item.packing_recommendation
              ? {
                  ...item,
                  packing_recommendation: {
                    ...item.packing_recommendation,
                    is_accepted: isAccepted,
                  },
                }
              : item,
          ),
        );
      } catch (error) {
        console.error("Error updating recommendation acceptance:", error);
        throw error;
      }
    },
    [tripId],
  );

  // Multiples of the same classes are allowed (e.g. two "top" scans)
  useEffect(() => {
    if (!currentItem) return;

    const id = currentItem.item_id;
    const name = currentItem.item_name;

    // If this item_id is already in scannedItems, update it; otherwise append
    setScannedItems((prev) => {
      const i = prev.findIndex((item) => item.item_id === id);
      if (i !== -1) {
        const next = [...prev];
        next[i] = currentItem;
        return next;
      }
      return [...prev, currentItem];
    });

    // New scan of this class should consume ONE recommendation entry (if present)
    setRecommendedItems((recs) => {
      const idx = recs.findIndex((rec) => rec.item_name === name);
      if (idx === -1) return recs;
      const next = [...recs];
      next.splice(idx, 1);
      return next;
    });

    if (currentItem.packing_recommendation?.status === "pack") {
      void packItem(currentItem.item_id);
    }
  }, [currentItem, packItem]);

  const toggleItem = useCallback(
    async (id: string) => {
      // Undo acceptance on any pack/unpack toggle so the pill can reappear
      const item = scannedItems.find((i) => i.item_id === id);
      const rec = item?.packing_recommendation;
      if (tripId && rec?.is_accepted && rec.recommendation_id) {
        await setRecommendationAccepted(id, rec.recommendation_id, false);
      }

      const isChecked = checkedItems.has(id);
      if (isChecked) {
        await unpackItem(id);
      } else {
        await packItem(id);
      }
    },
    [
      checkedItems,
      packItem,
      scannedItems,
      setRecommendationAccepted,
      tripId,
      unpackItem,
    ],
  );

  const updateItemQuantity = useCallback(
    async (itemId: string, quantity: number) => {
      if (!tripId) return;

      // Find previous quantity and item name for this scanned item
      const prevItem = scannedItems.find((i) => i.item_id === itemId);
      const prevQty = prevItem?.quantity ?? 1;
      const itemName = prevItem?.item_name;

      try {
        const response = await apiFetch(
          `/items/${encodeURIComponent(itemId)}`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ quantity }),
          },
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        // Keep local list in sync
        setScannedItems((prev) =>
          prev.map((item) =>
            item.item_id === itemId ? { ...item, quantity } : item,
          ),
        );

        // If quantity increased, consume that many recommendations of the same name
        if (itemName && quantity > prevQty) {
          const delta = quantity - prevQty;
          setRecommendedItems((recs) =>
            removeNRecommendedItemsByName(recs, itemName, delta),
          );
        }

        if (onTripChanged) {
          await onTripChanged();
        }
      } catch (error) {
        console.error("Error updating item quantity:", error);
        throw error;
      }
    },
    [tripId, onTripChanged, scannedItems],
  );

  return {
    recommendedItems,
    scannedItems,
    checkedItems,
    toggleItem,
    packItem,
    unpackItem,
    updateItemQuantity,
    setRecommendationAccepted,
  };
}
