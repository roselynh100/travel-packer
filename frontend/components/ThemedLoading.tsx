import { ThemedText } from "@/components/ThemedText";
import { ActivityIndicator, Modal, View } from "react-native";
import { useTheme } from "@/theme/useTheme";

export function ThemedLoading({
  isLoading,
  message,
}: {
  isLoading: boolean;
  message: string;
}) {
  const theme = useTheme();

  return (
    <Modal visible={isLoading} transparent={true} animationType="fade">
      <View className="flex-1 justify-center items-center gap-8 bg-black/70">
        <ActivityIndicator size="large" color={theme.primary} />
        <ThemedText type="subtitle" style={{ color: "white" }}>
          {message}
        </ThemedText>
      </View>
    </Modal>
  );
}
