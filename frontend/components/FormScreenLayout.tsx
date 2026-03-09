import type { ReactNode } from "react";
import {
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  View,
} from "react-native";

import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { ThemedLoading } from "@/components/ThemedLoading";
import { cn } from "@/helpers/cn";
import { useTheme } from "@/theme/useTheme";
import { ScreenScroll } from "@/components/ScreenScroll";

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
  const theme = useTheme();

  const Wrapper = Platform.OS === "web" ? View : Pressable;
  const wrapperProps =
    Platform.OS === "web"
      ? { className: "flex-1" }
      : { className: "flex-1", onPress: Keyboard.dismiss };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      className="flex-1"
    >
      <Wrapper {...wrapperProps}>
        <View className="flex-1" style={{ backgroundColor: theme.bg }}>
          <ScreenScroll variant="spaceBetween">
            <View className="flex-col gap-6">
              <ThemedText type="title">{title}</ThemedText>
              {children}
            </View>
          </ScreenScroll>
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
