import { useEffect, useState } from "react";
import { Platform, ScrollView, View } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { API_BASE_URL } from "@/constants/api";
import { RecommendedItem } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedButton } from "@/components/ThemedButton";
import { useRouter } from "expo-router";

export default function PackingList() {
  const { tripId } = useAppContext();
  const router = useRouter();

  const [recommendedItems, setRecommendedItems] = useState<RecommendedItem[]>(
    []
  );
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/trips/${tripId}/recommendations`,
          { method: "POST" }
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

    fetchTrips();
  }, [tripId]);

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
