import { useEffect, useState } from "react";
import { Platform, Pressable, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import { ScreenScroll } from "@/components/ScreenScroll";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { useAppContext } from "@/helpers/AppContext";
import { cn } from "@/helpers/cn";
import { useTheme } from "@/theme/useTheme";
import { ItemWithPackingRecommendation } from "@/constants/types";
import {
  PackingListItem,
  PackingListPill,
  PackingRecommendationModal,
} from "@/components/packing";
import { averageTemp } from "@/helpers/averageTemp";
import { useTripInfo } from "@/hooks/useTripInfo";
import { usePackingList } from "@/hooks/usePackingList";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";

export default function Trips() {
  const router = useRouter();
  const theme = useTheme();

  const { tripId, currentItem } = useAppContext();

  const { tripInfo, refetch: refetchTripInfo } = useTripInfo(tripId);

  const {
    recommendedItems,
    scannedItems,
    checkedItems,
    toggleItem: handleToggleItem,
    packItem,
    unpackItem,
  } = usePackingList(tripId, currentItem, {
    onTripChanged: refetchTripInfo,
  });

  const [selectedPackingItem, setSelectedPackingItem] =
    useState<ItemWithPackingRecommendation | null>(
      (currentItem as ItemWithPackingRecommendation) ?? null,
    );

  const { packingDecision } = useLocalSearchParams<{
    packingDecision?: string;
  }>();

  // If there's a packing decision in the URL, open modal for the last scanned item
  // Then reset URL params
  useEffect(() => {
    if (!packingDecision) return;
    if (currentItem) setSelectedPackingItem(currentItem);

    router.setParams({ packingDecision: undefined });
  }, [packingDecision, currentItem, router]);

  const secondaryAction = () => {
    if (!selectedPackingItem?.item_id) return;

    void packItem(selectedPackingItem.item_id);
    setSelectedPackingItem(null);
  };

  const primaryAction = () => {
    if (selectedPackingItem?.packing_recommendation?.status === "remove") {
      void unpackItem(selectedPackingItem.item_id);
    } else if (selectedPackingItem?.packing_recommendation?.status === "swap") {
      const swapCandidates =
        selectedPackingItem.packing_recommendation.swap_candidates;

      // Unpack swap candidates
      for (const candidate of swapCandidates ?? []) {
        void unpackItem(candidate.item_id);
      }
      // Pack selected item
      void packItem(selectedPackingItem.item_id);
    }
    setSelectedPackingItem(null);
  };

  return (
    <ScreenScroll>
      <ThemedText type="title">Your trip</ThemedText>

      {tripId ? (
        <>
          <View className="mt-6 gap-6">
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
              {/* Scanned items */}
              {scannedItems.length > 0 && (
                <>
                  <View className="flex-row items-center justify-between">
                    <ThemedText type="defaultSemiBold">
                      Scanned items
                    </ThemedText>
                    <Pressable
                      className="py-2 px-4 rounded-2xl"
                      style={{ backgroundColor: theme.primary }}
                      onPress={() =>
                        alert("(display packing optimization score)")
                      }
                    >
                      <ThemedText
                        className="text-xs"
                        style={{ color: "white" }}
                      >
                        I&apos;m done packing!
                      </ThemedText>
                    </Pressable>
                  </View>
                  <View
                    className={cn(
                      "mb-4",
                      Platform.OS === "web" ? "" : "flex-col gap-2 mt-2",
                    )}
                  >
                    {scannedItems.map((item) => {
                      const id = item.item_id;
                      return (
                        <PackingListItem
                          key={id}
                          item={item}
                          checked={checkedItems.has(id)}
                          onToggle={() => handleToggleItem(id)}
                          onPressRecommendation={setSelectedPackingItem}
                          recommendationDismissed={dismissedRecommendationIds.has(
                            item.item_id,
                          )}
                        />
                      );
                    })}
                  </View>
                </>
              )}

              {/* Recommended items */}
              <ThemedText type="defaultSemiBold">Recommended items</ThemedText>
              <View
                className={Platform.OS === "web" ? "" : "flex-col gap-2 mt-2"}
              >
                {recommendedItems.map((item, i) => (
                  <ThemedCheckbox
                    key={i}
                    label={item.item_name}
                    disabled={true}
                  />
                ))}
              </View>
            </View>
          </View>
          <PackingRecommendationModal
            visible={selectedPackingItem !== null}
            item={selectedPackingItem}
            onSecondary={secondaryAction}
            onPrimary={primaryAction}
          />
        </>
      ) : (
        <>
          <View className="mt-[25vh] mb-8">
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
