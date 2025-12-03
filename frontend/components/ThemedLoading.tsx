import { ThemedText } from "@/components/ThemedText";
import { ActivityIndicator, Modal, View } from "react-native";

export function ThemedLoading({
  isLoading,
  message,
}: {
  isLoading: boolean;
  message: string;
}) {
  return (
    <Modal visible={isLoading} transparent={true} animationType="fade">
      <View className="flex-1 justify-center items-center gap-8 bg-black/70">
        <ActivityIndicator size="large" />
        <ThemedText type="subtitle" className="text-white">
          {message}
        </ThemedText>
      </View>
    </Modal>
  );
}
