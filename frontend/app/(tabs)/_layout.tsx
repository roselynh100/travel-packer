import { Tabs } from "expo-router";
import React from "react";

import { IconSymbol } from "@/components/ui/icon-symbol";
import { useAppContext } from "@/helpers/AppContext";
import { View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";

export default function TabLayout() {
  const { userId } = useAppContext();
  const theme = useTheme();

  return (
    <Tabs
      screenOptions={{
        header: () => (
          <View
            style={{ backgroundColor: theme.bgNav }}
            className="w-full p-4 flex-row items-center justify-between gap-4"
          >
            <ThemedText type="subtitle" className="flex-shrink-0">
              Packulus 🧳
            </ThemedText>
            {Boolean(userId) && (
              <ThemedText className="text-sm truncate">
                User:{"\n"}
                {userId}
              </ThemedText>
            )}
          </View>
        ),
        tabBarActiveTintColor: theme.tabSelected,
        tabBarStyle: {
          backgroundColor: theme.bgNav,
          borderTopWidth: 0,
        },
        sceneStyle: { backgroundColor: theme.bg },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Welcome",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="house.fill" color={color} />
          ),
        }}
      />

      <Tabs.Screen
        name="Trips"
        options={{
          title: "Trips",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="sun.max" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="Scan"
        options={{
          title: "Pack Items",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="camera.fill" color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
