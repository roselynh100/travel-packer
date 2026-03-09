import { View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedButton } from "@/components/ThemedButton";
import { useTheme } from "@/theme/useTheme";
import { ScreenScroll } from "@/components/ScreenScroll";

const steps = [
  {
    number: 1,
    title: "Input your trip information",
    detail: "Provide your destination, dates, and travel details.",
    icon: "sun.max" as const,
  },
  {
    number: 2,
    title: "Review your packing list",
    detail: "View suggested items for your trip.",
    icon: "list.bullet" as const,
  },
  {
    number: 3,
    title: "Pack your items",
    detail:
      "Weigh and scan your items to receive a recommendation: pack, don't pack, or swap!",
    icon: "camera.fill" as const,
  },
];

export default function Welcome() {
  const theme = useTheme();

  return (
    <ScreenScroll>
      {/* Hero */}
      <View className="items-center mb-8">
        <View className="pt-6 pb-4">
          <IconSymbol name="cube.box.fill" size={44} color={theme.primary} />
        </View>
        <ThemedText type="title" className="text-center">
          Welcome to Packulus.
        </ThemedText>
        <ThemedText className="text-center mt-4">
          Pack smarter with weight tracking and smart recommendations!
        </ThemedText>
      </View>

      {/* Steps */}
      <View className="gap-6">
        {steps.map((step) => (
          <View
            key={step.number}
            className="p-4 rounded-2xl"
            style={{ backgroundColor: theme.bgNav }}
          >
            <View className="flex-1">
              <View className="flex-row gap-2">
                <IconSymbol name={step.icon} size={22} color={theme.primary} />
                <ThemedText type="defaultSemiBold" className="mb-1">
                  {step.title}
                </ThemedText>
              </View>
              <ThemedText className="text-sm">{step.detail}</ThemedText>
            </View>
          </View>
        ))}
        <ThemedButton title="Get started" />
      </View>
    </ScreenScroll>
  );
}
