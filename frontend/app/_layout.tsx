import "../global.css";
import "react-native-reanimated";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaView } from "react-native-safe-area-context";
import { useColorScheme } from "react-native";

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <>
      <SafeAreaView
        className={colorScheme === "dark" ? "dark flex-1" : "flex-1"}
      >
        <Stack>
          <Stack.Screen
            name="(tabs)"
            options={{
              title: "Packulus 🧳",
            }}
          />
        </Stack>
      </SafeAreaView>
      <StatusBar style="auto" />
    </>
  );
}
