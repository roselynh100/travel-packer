import type { ReactNode } from "react";
import {
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  useColorScheme,
  View,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { ThemedLoading } from "@/components/ThemedLoading";
import { cn } from "@/helpers/cn";

type FormScreenLayoutProps = {
  title: string;
  children: ReactNode;
  onSave: () => void | Promise<void>;
  saveDisabled?: boolean;
  isLoading?: boolean;
  loadingMessage?: string;
};

export function FormScreenLayout({
  title,
  children,
  onSave,
  saveDisabled = false,
  isLoading = false,
  loadingMessage = "Saving...",
}: FormScreenLayoutProps) {
  const Wrapper = Platform.OS === "web" ? View : Pressable;
  const wrapperProps =
    Platform.OS === "web"
      ? { className: "flex-1" }
      : { className: "flex-1", onPress: Keyboard.dismiss };

  const colorScheme = useColorScheme();
  const fadeColor = colorScheme === "dark" ? "#141414" : "#ffffff";

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      className="flex-1"
    >
      <Wrapper {...wrapperProps}>
        <View className="flex-1">
          <ScrollView
            contentContainerStyle={{
              flexGrow: 1,
              justifyContent: "space-between",
            }}
            className={Platform.OS === "web" ? "p-12" : "p-6"}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            <View className="flex-col gap-6">
              <ThemedText type="title">{title}</ThemedText>
              {children}
            </View>
          </ScrollView>
          <LinearGradient
            colors={["transparent", fadeColor] as const}
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: 80,
              pointerEvents: "none",
            }}
          />
        </View>
        <ThemedButton
          title="Save"
          onPress={onSave}
          disabled={saveDisabled}
          className={cn(
            Platform.OS === "web" ? "mx-12 mb-12 mt-6" : "mx-6 my-6",
            saveDisabled && "opacity-50",
          )}
        />
        <ThemedLoading isLoading={isLoading} message={loadingMessage} />
      </Wrapper>
    </KeyboardAvoidingView>
  );
}
