import { View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { ThemedButton } from "@/components/ThemedButton";
import { ScreenScroll } from "@/components/ScreenScroll";

export function Success({ onContinue }: { onContinue: () => void }) {
  return (
    <ScreenScroll>
      <View className="mt-[40%] mb-8">
        <ThemedText type="title" className="text-center">
          Trip generated ✅
        </ThemedText>
        <ThemedText className="text-center mt-4">
          Start packing for your trip!
        </ThemedText>
      </View>

      <ThemedButton title="View trip" onPress={onContinue} />
    </ScreenScroll>
  );
}
