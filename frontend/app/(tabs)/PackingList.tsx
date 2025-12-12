import { useCallback, useEffect, useState } from "react";
import { Platform, ScrollView, View } from "react-native";
import { useRouter } from "expo-router";

import { ThemedText } from "@/components/ThemedText";
import { API_BASE_URL } from "@/constants/api";
import {
  RecommendedItem,
  Trip,
  PackingListItem as PackingListItemType,
} from "@/constants/types";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedButton } from "@/components/ThemedButton";
import { PackingListItem } from "@/components/PackingListItem";
import { PackingListPill } from "@/components/PackingListPill";

export default function PackingList() {
  const { tripId, currentItem } = useAppContext();
  const router = useRouter();

  // Unified list that can contain both RecommendedItem and Item
  const [packingListItems, setPackingListItems] = useState<
    PackingListItemType[]
  >([]);
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());
  const [tripInfo, setTripInfo] = useState<Trip | null>(null);

  // Only re-fetch recommendations when the tripId changes
  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!tripId) return;

      try {
        const response = await fetch(
          `${API_BASE_URL}/trips/${tripId}/recommendations`
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`
          );
        }

        const result: RecommendedItem[] = await response.json();
        setPackingListItems(result);
        console.log("Fetched recommendations:", result);
      } catch (error) {
        console.error("Error fetching recommendations:", error);
      }
    };

    fetchRecommendations();
  }, [tripId]);

  const fetchTripInfo = useCallback(async () => {
    if (!tripId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/trips/${tripId}`);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API error (${response.status}): ${errorText || response.statusText}`
        );
      }

      const result: Trip = await response.json();
      setTripInfo(result);
      console.log("Fetched trip info:", result);
    } catch (error) {
      console.error("Error fetching trip info:", error);
    }
  }, [tripId]);

  // Re-fetch trip info when tripId changes
  useEffect(() => {
    fetchTripInfo();
  }, [tripId, fetchTripInfo]);

  const packItem = useCallback(
    async (itemId: string) => {
      if (!tripId) return;

      try {
        const response = await fetch(
          `${API_BASE_URL}/trips/${tripId}/item/${itemId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`
          );
        }

        const result = await response.json();
        console.log("Item packed:", result);

        // Check item
        setCheckedItems((prev) => new Set(prev).add(itemId));

        // Update bag info
        await fetchTripInfo();
      } catch (error) {
        console.error("Error packing item:", error);
        throw error;
      }
    },
    [tripId, fetchTripInfo]
  );

  const unpackItem = useCallback(
    async (itemId: string) => {
      if (!tripId) return;

      try {
        const response = await fetch(
          `${API_BASE_URL}/trips/${tripId}/item/${itemId}`,
          {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`
          );
        }

        const result = await response.json();
        console.log("Item unpacked:", result);

        // Uncheck item
        setCheckedItems((prev) => {
          const next = new Set(prev);
          next.delete(itemId);
          return next;
        });

        // Update bag info
        await fetchTripInfo();
      } catch (error) {
        console.error("Error unpacking item:", error);
        throw error;
      }
    },
    [tripId, fetchTripInfo]
  );

  // Add currentItem to the list, merging with existing items by name
  useEffect(() => {
    if (currentItem && "item_id" in currentItem) {
      setPackingListItems((prev) => {
        // Overwrite existing items with new info
        const existingIndexById = prev.findIndex(
          (item) => "item_id" in item && item.item_id === currentItem.item_id
        );

        if (existingIndexById !== -1) {
          const newItems = [...prev];
          newItems[existingIndexById] = currentItem;
          return newItems;
        }

        // Merge items with the same name (overwrite recommended items with more complete info)
        const existingIndexByName = prev.findIndex(
          (item) => item.item_name === currentItem.item_name
        );

        if (existingIndexByName !== -1) {
          const newItems = [...prev];
          newItems[existingIndexByName] = currentItem;
          return newItems;
        }

        // Add new item if not already in list
        return [...prev, currentItem];
      });

      if (currentItem.packing_recommendation === "pack") {
        packItem(currentItem.item_id);
      }
    }
  }, [currentItem, packItem]);

  const handleToggleItem = async (id: string) => {
    const isChecked = checkedItems.has(id);

    if (isChecked) {
      await unpackItem(id);
    } else {
      await packItem(id);
    }
  };

  return (
    <ScrollView
      contentContainerStyle={{
        flexGrow: 1,
        justifyContent: "space-between",
      }}
      className={Platform.OS === "web" ? "p-12" : "p-6"}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <View className="flex-col">
        <ThemedText type="title" className="mb-6">
          Packing List 📜
        </ThemedText>
        {tripId ? (
          <>
            <View className="gap-2 mb-2">
              <ThemedText>Trip ID: {tripId}</ThemedText>
              <View
                className={
                  Platform.OS === "web"
                    ? "flex-row gap-4"
                    : "flex-col gap-2 items-start"
                }
              >
                <PackingListPill
                  type="weight"
                  value={tripInfo?.total_items_weight || 0}
                />
                <PackingListPill
                  type="volume"
                  value={tripInfo?.total_items_volume || 0}
                />
              </View>
            </View>
            <View className="gap-4">
              {packingListItems?.map((item, i) => {
                const id = "item_id" in item ? item.item_id : String(i);
                return (
                  <PackingListItem
                    key={i}
                    item={item}
                    checked={checkedItems.has(id)}
                    onToggle={() => handleToggleItem(id)}
                  />
                );
              })}
            </View>
          </>
        ) : (
          <ThemedText type="subtitle">There is no current trip!</ThemedText>
        )}
      </View>

      {!tripId && (
        <ThemedButton
          title="Add trip details"
          variant="outline"
          onPress={() => router.push("/TripInfo")}
        />
      )}
    </ScrollView>
  );
}
