import { ScrollView, View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { IconSymbol } from "@/components/ui/icon-symbol";

const steps = [
  {
    number: 1,
    title: "Input your trip information",
    detail:
      "Go to the Trip Info tab and add your destination, dates, and travel details.",
    icon: "sun.max" as const,
  },
  {
    number: 2,
    title: "Review your packing list",
    detail:
      "Check out the Packing List tab to see suggested items for your trip.",
    icon: "list.bullet" as const,
  },
  {
    number: 3,
    title: "Scan your items",
    detail:
      "First, connect the scale and make sure nothing's on it. Then, open the Pack Items tab take a photo to scan your items one at a time.",
    icon: "camera.fill" as const,
  },
  {
    number: 4,
    title: "Receive a packing recommendation",
    detail: "Get a tailored recommendation based on your items and trip.",
    icon: "cube.box.fill" as const,
  },
];

export default function Welcome() {
  return (
    <ScrollView
      className="flex-1"
      contentContainerStyle={{ flexGrow: 1, paddingBottom: 32 }}
      showsVerticalScrollIndicator={false}
    >
      <View className="px-6 pt-8 pb-6">
        {/* Hero */}
        <View className="items-center mb-10">
          <View className="w-20 h-20 bg-[var(--color-primary)]/20 items-center justify-center mb-4">
            <IconSymbol
              name="cube.box.fill"
              size={44}
              color="var(--color-primary)"
            />
          </View>
          <ThemedText type="title" className="text-center">
            Welcome to Packulus.
          </ThemedText>
          <ThemedText className="text-center mt-2 opacity-80 max-w-xs">
            Pack smarter with weight tracking and smart recommendations!
          </ThemedText>
        </View>

        {/* Steps */}
        <ThemedText type="subtitle" className="mb-4">
          How it works
        </ThemedText>
        <View className="gap-6">
          {steps.map((step) => (
            <View
              key={step.number}
              className="flex-row gap-4 p-4 rounded-2xl bg-[var(--color-bg-nav)]"
            >
              <View className="w-10 h-10 rounded-full bg-[var(--color-primary)] items-center justify-center">
                <ThemedText className="text-white font-bold text-lg">
                  {step.number}
                </ThemedText>
              </View>
              <View className="flex-1">
                <View className="flex-row gap-2">
                  <IconSymbol
                    name={step.icon}
                    size={22}
                    color="var(--color-primary)"
                  />
                  <ThemedText type="defaultSemiBold" className="mb-1">
                    {step.title}
                  </ThemedText>
                </View>
                <ThemedText className="text-sm">{step.detail}</ThemedText>
              </View>
            </View>
          ))}
        </View>
      </View>
    </ScrollView>
  );
}
