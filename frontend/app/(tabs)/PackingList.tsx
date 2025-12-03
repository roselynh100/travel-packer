import { useCallback, useEffect, useState } from "react";
import { Platform, ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";

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
  const { tripId } = useAppContext();
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

  // Re-fetch bag info when tripId changes and when re-visiting this screen
  useFocusEffect(
    useCallback(() => {
      if (!tripId) return;

      const fetchTripInfo = async () => {
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
      };

      fetchTripInfo();
    }, [tripId])
  );

  async function packItem(itemId: string) {
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
    } catch (error) {
      throw error;
    }
  }

  const handleToggleItem = (id: string) => {
    setCheckedItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id); // uncheck
      } else {
        next.add(id);
        packItem(id);
      }
      return next;
    });
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
              <View className="flex-row gap-4">
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
