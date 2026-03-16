import { useCallback, useEffect, useState } from "react";

import {
  ItemWithPackingRecommendation,
  RecommendedItem,
} from "@/constants/types";
import { apiFetch } from "@/constants/api";

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

  // Multiples of the same classes are allowed (e.g. two "top" scans)
  useEffect(() => {
    if (!currentItem) return;

    const id = currentItem.item_id;
    const name = currentItem.item_name;

    // If this item_id is already in scannedItems, update it
    setScannedItems((prev) => {
      const i = prev.findIndex((item) => item.item_id === id);
      if (i !== -1) {
        const next = [...prev];
        next[i] = currentItem;
        return next;
      }
      return [...prev, currentItem];
    });

    // Remove the matching recommendedItem from recommendedItems
    setRecommendedItems((recs) => recs.filter((rec) => rec.item_name !== name));

    if (currentItem.packing_recommendation?.status === "pack") {
      void packItem(currentItem.item_id);
    }
  }, [currentItem, packItem]);

  const toggleItem = useCallback(
    async (id: string) => {
      const isChecked = checkedItems.has(id);
      if (isChecked) {
        await unpackItem(id);
      } else {
        await packItem(id);
      }
    },
    [checkedItems, packItem, unpackItem],
  );

  const updateItemQuantity = useCallback(
    async (itemId: string, quantity: number) => {
      if (!tripId) return;

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

        if (onTripChanged) {
          await onTripChanged();
        }
      } catch (error) {
        console.error("Error updating item quantity:", error);
        throw error;
      }
    },
    [tripId, onTripChanged],
  );

  return {
    recommendedItems,
    scannedItems,
    checkedItems,
    toggleItem,
    packItem,
    unpackItem,
    updateItemQuantity,
  };
}
