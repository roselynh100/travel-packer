import "../global.css";
import "react-native-reanimated";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaView } from "react-native-safe-area-context";
import { useColorScheme } from "react-native";
import { cn } from "@/helpers/cn";

export default function RootLayout() {
  const colorScheme = useColorScheme();
  return (
    <>
      <SafeAreaView
        className={cn("flex-1", colorScheme === "dark" ? "dark" : "")}
      >
        <Stack>
          <Stack.Screen
            name="(tabs)"
            options={{
              title: "Packulus 🧳",
              headerStyle: {
                backgroundColor: "var(--color-bg-nav)",
              },
              headerTitleStyle: { color: "var(--color-text)" },
              headerShadowVisible: false,
            }}
          />
        </Stack>
      </SafeAreaView>
      <StatusBar style="auto" />
    </>
  );
}
