import { Tabs } from "expo-router";
import React from "react";

import { IconSymbol } from "@/components/ui/icon-symbol";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: "var(--color-tab-selected)",
        tabBarStyle: {
          backgroundColor: "var(--color-bg-nav)",
          borderTopWidth: 0,
        },
        sceneStyle: { backgroundColor: "var(--color-bg)" },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "User Info",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="house.fill" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="TripInfo"
        options={{
          title: "Trip Info",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="sun.max" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="PackingList"
        options={{
          title: "Packing List",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={28} name="list.bullet" color={color} />
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
