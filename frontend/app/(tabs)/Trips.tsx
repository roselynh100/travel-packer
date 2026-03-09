import { Platform, View } from "react-native";
import { useEffect, useState } from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { ScreenScroll } from "@/components/ScreenScroll";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { useAppContext } from "@/helpers/AppContext";
import { useTheme } from "@/theme/useTheme";
import {
  ItemWithPackingRecommendation,
  PackingListItem as PackingListItemType,
} from "@/constants/types";
import {
  PackingListItem,
  PackingListPill,
  PackingRecommendationModal,
} from "@/components/packing";
import { averageTemp } from "@/helpers/averageTemp";
import { useTripInfo } from "@/hooks/useTripInfo";
import { usePackingList } from "@/hooks/usePackingList";

export default function Trips() {
  const router = useRouter();
  const theme = useTheme();
  const { packingDecision } = useLocalSearchParams<{
    packingDecision?: string;
  }>();
  const [packingModalVariant, setPackingModalVariant] = useState<
    "remove" | "swap" | null
  >(null);

  const { tripId, currentItem } = useAppContext();

  const { tripInfo, refetch: refetchTripInfo } = useTripInfo(tripId);

  const {
    items: packingListItems,
    checkedItems,
    toggleItem: handleToggleItem,
  } = usePackingList(tripId, currentItem as PackingListItemType | null, {
    onTripChanged: refetchTripInfo,
  });

  useEffect(() => {
    if (packingDecision === "remove" || packingDecision === "swap") {
      setPackingModalVariant(packingDecision as "remove" | "swap");

      // Remove the packing decision from the URL
      router.setParams({ packingDecision: undefined });
    }
  }, [packingDecision, router]);

  return (
    <ScreenScroll>
      <ThemedText type="title">Your trip</ThemedText>

      {tripId ? (
        <View className="mt-6 gap-6">
          <PackingRecommendationModal
            visible={packingModalVariant !== null}
            variant={packingModalVariant}
            itemName={
              (currentItem as ItemWithPackingRecommendation | null)?.item_name
            }
            onIgnore={() => setPackingModalVariant(null)}
            onPrimary={() => setPackingModalVariant(null)}
          />
          <View className="flex-row gap-2">
            <PackingListPill
              type="weight"
              value={tripInfo?.total_items_weight || 0}
            />
            <PackingListPill
              type="volume"
              value={tripInfo?.total_items_volume || 0}
            />
          </View>

          {/* Top row */}
          <View className="flex-row gap-4">
            <View
              className="rounded-2xl p-4"
              style={{ backgroundColor: theme.bgNav, flex: 2 }}
            >
              <ThemedText type="defaultSemiBold">Average temp</ThemedText>
              <ThemedText type="subtitle" className="text-center mt-2">
                {averageTemp(tripInfo?.lowest_temp, tripInfo?.highest_temp)}
              </ThemedText>
            </View>
            <View
              className="rounded-2xl p-4"
              style={{ backgroundColor: theme.bgNav, flex: 3 }}
            >
              <ThemedText type="defaultSemiBold">Activities</ThemedText>
              <ThemedText className="text-sm mt-2">
                {tripInfo?.activities?.join(", ") || "No activities planned"}
              </ThemedText>
            </View>
          </View>

          {/* Packing list box */}
          <View
            className="rounded-2xl p-4"
            style={{ backgroundColor: theme.bgNav }}
          >
            <ThemedText type="defaultSemiBold">Packing list</ThemedText>
            <View
              className={Platform.OS === "web" ? "" : "flex-col gap-2 mt-2"}
            >
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
          </View>
        </View>
      ) : (
        <>
          <View className="mt-[30%] mb-8">
            <ThemedText type="title" className="text-center">
              No trips right now
            </ThemedText>
            <ThemedText className="text-center mt-4">
              Generate a trip to start packing smarter.
            </ThemedText>
          </View>
          <ThemedButton title="Add new trip" onPress={() => router.push("/")} />
        </>
      )}
    </ScreenScroll>
  );
}
