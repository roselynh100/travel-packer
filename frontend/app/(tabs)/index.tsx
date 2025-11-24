import { useState } from "react";
import {
  ActivityIndicator,
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
import { Checkbox } from "expo-checkbox";

export default function HomeScreen() {
  const router = useRouter();

  const [destination, onChangeDestination] = useState("");
  const [dates, onChangeDates] = useState("");
  const [laundry, onChangeLaundry] = useState(false);
  const [activities, onChangeActivities] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSave = async () => {
    setIsLoading(true);

    // Wait for 5 seconds
    await new Promise((resolve) => setTimeout(resolve, 5000));

    // Navigate to list page
    router.push("/PackingList");
    setIsLoading(false);
  };

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

            <View className="flex-row gap-4">
              <Checkbox
                value={laundry}
                onValueChange={onChangeLaundry}
                color="var(--color-primary)"
                className="w-6 h-6"
              />
              <ThemedText type="subtitle">
                I am planning to do laundry
              </ThemedText>
            </View>
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
