import { useCallback, useEffect, useState } from "react";

import {
  PackingListItem as PackingListItemType,
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
  items: PackingListItemType[];
  checkedItems: Set<string>;
  toggleItem: (id: string) => Promise<void>;
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
  currentItem: PackingListItemType | null | undefined,
  options: UsePackingListOptions = {},
): UsePackingListResult {
  const { onTripChanged } = options;

  const [items, setItems] = useState<PackingListItemType[]>([]);
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());

  // Initial recommendations fetch whenever tripId changes
  useEffect(() => {
    if (!tripId) return;

    setItems([]);
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
        setItems(result);
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

        setCheckedItems((prev) => new Set(prev).add(itemId));

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

        setCheckedItems((prev) => {
          const next = new Set(prev);
          next.delete(itemId);
          return next;
        });

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

  // Merge currentItem into list when it changes
  // TODO: might rework this with duplicate items -> quantity
  useEffect(() => {
    if (!currentItem || !("item_id" in currentItem)) return;

    setItems((prev) => {
      // Overwrite existing items with new info by id
      const existingIndexById = prev.findIndex(
        (item) => "item_id" in item && item.item_id === currentItem.item_id,
      );

      if (existingIndexById !== -1) {
        const newItems = [...prev];
        newItems[existingIndexById] = currentItem;
        return newItems;
      }

      // Merge items with the same name (overwrite recommended items with more complete info)
      const existingIndexByName = prev.findIndex(
        (item) => item.item_name === currentItem.item_name,
      );

      if (existingIndexByName !== -1) {
        const newItems = [...prev];
        newItems[existingIndexByName] = currentItem;
        return newItems;
      }

      // Add new item if not already in list
      return [...prev, currentItem];
    });

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

  return { items, checkedItems, toggleItem };
}
