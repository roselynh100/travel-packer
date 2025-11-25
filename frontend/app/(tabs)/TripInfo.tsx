import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  View,
} from "react-native";
import { useRouter } from "expo-router";

import { ThemedText } from "@/components/ThemedText";
import { ThemedTextInput } from "@/components/ThemedTextInput";
import { ThemedButton } from "@/components/ThemedButton";
import { API_BASE_URL } from "@/constants/api";
import { Trip } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { useAppContext } from "@/helpers/AppContext";

export default function TripInfo() {
  const router = useRouter();

  const [destination, onChangeDestination] = useState("");
  const [dates, onChangeDates] = useState("");
  const [laundry, onChangeLaundry] = useState(false);
  const [activities, onChangeActivities] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { setTripId } = useAppContext();

  async function handleSave() {
    try {
      setIsLoading(true);

      const trip: Trip = {
        destination,
        duration_days: 5, // TODO: fix, currently hardcoded, figure out date input
        doing_laundry: laundry,
        activities,
      };

      await saveToAPI(trip);
      await new Promise((resolve) => setTimeout(resolve, 5000));

      router.push("/PackingList");
    } catch (error) {
      console.error("Error saving trip details:", error);
      Alert.alert(
        "Error",
        error instanceof Error ? error.message : "Failed to save trip details"
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function saveToAPI(tripInput: Trip) {
    try {
      const response = await fetch(`${API_BASE_URL}/trips`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(tripInput),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API error (${response.status}): ${errorText || response.statusText}`
        );
      }

      const result: Trip = await response.json();
      console.log("Save success:", result);
      setTripId(result.trip_id ?? "No trip id saved");
    } catch (error) {
      throw error;
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      className="flex-1"
    >
      <Pressable
        onPress={Platform.OS === "web" ? undefined : Keyboard.dismiss}
        className="flex-1"
      >
        <View className="flex-1 justify-between p-12">
          <Modal visible={isLoading} transparent={true} animationType="fade">
            <View className="flex-1 justify-center items-center gap-8 bg-black/70">
              <ActivityIndicator size="large" />
              <ThemedText type="subtitle">Saving your trip...</ThemedText>
            </View>
          </Modal>
          <View className="flex-col gap-12">
            <ThemedText type="title">Input your trip details 🌴</ThemedText>
            <View className="gap-4">
              <ThemedText type="subtitle">Destination</ThemedText>
              <ThemedTextInput
                value={destination}
                onChangeText={onChangeDestination}
                placeholder="Toronto, Canada"
              />
            </View>

            <View className="gap-4">
              <ThemedText type="subtitle">Trip Dates</ThemedText>
              <ThemedTextInput
                value={dates}
                onChangeText={onChangeDates}
                placeholder="May 1, 2026 - May 31, 2026"
              />
            </View>

            <View className="gap-4">
              <ThemedText type="subtitle">
                Activities Planned (Optional)
              </ThemedText>
              <ThemedTextInput
                value={activities}
                onChangeText={onChangeActivities}
                placeholder="Hiking, Fancy Dinner, Clubbing..."
              />
            </View>

            <ThemedCheckbox
              label="I am planning to do laundry"
              value={laundry}
              onValueChange={onChangeLaundry}
              size="medium"
            />
          </View>

          <ThemedButton
            title="Save"
            onPress={handleSave}
            className="justify-end"
          />
        </View>
      </Pressable>
    </KeyboardAvoidingView>
  );
}
