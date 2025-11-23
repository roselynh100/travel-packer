import { useState } from "react";
import {
  ActivityIndicator,
  Button,
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  ScrollView,
  TouchableWithoutFeedback,
  View,
} from "react-native";
import { useRouter } from "expo-router";

import { ThemedText } from "@/components/ThemedText";
import { ThemedTextInput } from "@/components/ThemedTextInput";

export default function HomeScreen() {
  const router = useRouter();

  const [destination, onChangeDestination] = useState("");
  const [dates, onChangeDates] = useState("");
  const [activities, onChangeActivities] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSave = async () => {
    setIsLoading(true);

    // Wait for 5 seconds
    await new Promise((resolve) => setTimeout(resolve, 5000));

    // Navigate to list page
    router.push("/list");
    setIsLoading(false);
  };

  return (
    <KeyboardAvoidingView>
      <ScrollView keyboardShouldPersistTaps="handled">
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View className="flex flex-col gap-4 p-12">
            <Modal visible={isLoading} transparent={true} animationType="fade">
              <View className="flex-1 justify-center items-center gap-8 bg-black/70">
                <ActivityIndicator size="large" />
                <ThemedText type="subtitle">Saving your trip...</ThemedText>
              </View>
            </Modal>

            <ThemedText type="title">Input your trip details</ThemedText>

            <ThemedText type="subtitle">Destination</ThemedText>
            <ThemedTextInput
              value={destination}
              onChangeText={onChangeDestination}
              placeholder="Toronto, Canada"
            />

            <ThemedText type="subtitle">Trip Dates</ThemedText>
            <ThemedTextInput
              value={dates}
              onChangeText={onChangeDates}
              placeholder="May 1, 2026 - May 31, 2026"
            />

            <ThemedText type="subtitle">
              Activities Planned (Optional)
            </ThemedText>
            <ThemedTextInput
              value={activities}
              onChangeText={onChangeActivities}
              placeholder="Hiking, Fancy Dinner, Clubbing..."
            />

            <Button title="Save" onPress={handleSave} />
          </View>
        </TouchableWithoutFeedback>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
