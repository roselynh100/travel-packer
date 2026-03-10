import "../global.css";
import "react-native-reanimated";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import {
  SafeAreaProvider,
  useSafeAreaInsets,
} from "react-native-safe-area-context";
import { View } from "react-native";
import { useTheme } from "@/theme/useTheme";
import {
  StackSansText_400Regular,
  useFonts,
} from "@expo-google-fonts/stack-sans-text";
import * as SplashScreen from "expo-splash-screen";
import { AppProvider } from "@/helpers/AppContext";
import { useEffect } from "react";

SplashScreen.preventAutoHideAsync();

function RootContainer({ children }: { children: React.ReactNode }) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <View
      style={{ flex: 1, paddingTop: insets.top, backgroundColor: theme.bg }}
    >
      {children}
    </View>
  );
}

export default function RootLayout() {
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
      <SafeAreaProvider>
        <RootContainer>
          <Stack>
            <Stack.Screen
              name="(tabs)"
              options={{
                headerShown: false,
              }}
            />
          </Stack>
        </RootContainer>
      </SafeAreaProvider>
      <StatusBar style="auto" />
    </AppProvider>
  );
}
