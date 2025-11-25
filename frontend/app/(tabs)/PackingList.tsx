import { useEffect, useState } from "react";
import { View } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { API_BASE_URL } from "@/constants/api";
import { RecommendedItem } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
// import { useAppContext } from "@/helpers/AppContext";

const TRIP_ID = "e82e3d60-074c-427a-aa5c-95dd4d91e0f6";

export default function PackingList() {
  const [recommendedItems, setRecommendedItems] = useState<RecommendedItem[]>(
    []
  );
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());

  // const { tripId } = useAppContext();

  useEffect(() => {
    const fetchTrips = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/trips/${TRIP_ID}/recommendations`,
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
  }, []);

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
    <View className="flex flex-col gap-4 p-12">
      <ThemedText type="title">Packing List 📜</ThemedText>
      <ThemedText type="subtitle">Trip ID: {TRIP_ID}</ThemedText>
      {recommendedItems?.map((item, i) => (
        <ThemedCheckbox
          key={i}
          label={item.item_name}
          value={checkedItems.has(item.item_name)}
          onValueChange={() => toggleItem(item.item_name)}
        />
      ))}
    </View>
  );
}
