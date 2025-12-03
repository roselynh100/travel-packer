import { useCallback, useEffect, useState } from "react";
import { Platform, ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { useFocusEffect } from "@react-navigation/native";

import { ThemedText } from "@/components/ThemedText";
import { API_BASE_URL } from "@/constants/api";
import { RecommendedItem, Trip } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedButton } from "@/components/ThemedButton";

export default function PackingList() {
  const { tripId } = useAppContext();
  const router = useRouter();

  const [recommendedItems, setRecommendedItems] = useState<RecommendedItem[]>(
    []
  );
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
        setRecommendedItems(result);
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

  const toggleItem = (id: string) => {
    setCheckedItems((prev) => {
      const next = new Set(prev);

      if (next.has(id)) {
        next.delete(id); // uncheck
      } else {
        next.add(id); // check
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
            <View className="gap-4">
              <ThemedText>Trip ID: {tripId}</ThemedText>
              <ThemedText>
                Current bag weight: {tripInfo?.total_items_weight || 0} kg
              </ThemedText>
              <ThemedText>
                Current bag volume: {tripInfo?.total_items_volume || 0} cm3
              </ThemedText>
              {recommendedItems?.map((item, i) => (
                <ThemedCheckbox
                  key={i}
                  label={item.item_name}
                  value={checkedItems.has(item.item_name)}
                  onValueChange={() => toggleItem(item.item_name)}
                />
              ))}
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
