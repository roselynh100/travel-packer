import "../global.css";
import "react-native-reanimated";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaView } from "react-native-safe-area-context";
import { useColorScheme } from "react-native";
import {
  StackSansText_400Regular,
  useFonts,
} from "@expo-google-fonts/stack-sans-text";
import * as SplashScreen from "expo-splash-screen";
import { cn } from "@/helpers/cn";
import { AppProvider } from "@/helpers/AppContext";
import { useEffect } from "react";

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const colorScheme = useColorScheme();

  const [loaded, error] = useFonts({
    StackSansText_400Regular,
  });

  useEffect(() => {
    if (loaded || error) {
      SplashScreen.hideAsync();
    }
  }, [loaded, error]);

  if (!loaded && !error) {
    return null;
  }

  return (
    <AppProvider>
      <SafeAreaView
        edges={["top"]}
        className={cn("flex-1", colorScheme === "dark" ? "dark" : "")}
      >
        <Stack>
          <Stack.Screen
            name="(tabs)"
            options={{
              headerShown: false,
            }}
          />
        </Stack>
      </SafeAreaView>
      <StatusBar style="auto" />
    </AppProvider>
  );
}
