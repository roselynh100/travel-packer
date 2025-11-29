import { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  View,
} from "react-native";
import { useRouter } from "expo-router";

import { ThemedText } from "@/components/ThemedText";
import { ThemedTextInput } from "@/components/ThemedTextInput";
import { ThemedButton } from "@/components/ThemedButton";
import { API_BASE_URL } from "@/constants/api";
import { User } from "@/constants/types";
import { useAppContext } from "@/helpers/AppContext";

export default function HomeScreen() {
  const router = useRouter();

  const [name, onChangeName] = useState("");
  const [email, onChangeEmail] = useState("");
  const [password, onChangePassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { setUserId } = useAppContext();

  async function handleSave() {
    try {
      setIsLoading(true);

      const user: User = {
        name,
        email,
        password,
      };

      await saveToAPI(user);
      await new Promise((resolve) => setTimeout(resolve, 5000));

      router.push("/TripInfo");
    } catch (error) {
      console.error("Error creating user:", error);
      Alert.alert(
        "Error",
        error instanceof Error ? error.message : "Failed to create user"
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function saveToAPI(userInput: User) {
    try {
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userInput),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API error (${response.status}): ${errorText || response.statusText}`
        );
      }

      const result: User = await response.json();
      console.log("Save success:", result);
      setUserId(result.user_id ?? "No user id saved");
    } catch (error) {
      throw error;
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      className="flex-1"
    >
      <Pressable
        onPress={Platform.OS === "web" ? undefined : Keyboard.dismiss}
        className="flex-1"
      >
        <View className="flex-1 justify-between p-12">
          <Modal visible={isLoading} transparent={true} animationType="fade">
            <View className="flex-1 justify-center items-center gap-8 bg-black/70">
              <ActivityIndicator size="large" />
              <ThemedText type="subtitle">Saving your trip...</ThemedText>
            </View>
          </Modal>
          <View className="flex-col gap-12">
            <ThemedText type="title">Input your information 🤸</ThemedText>
            <View className="gap-4">
              <ThemedText type="subtitle">Name</ThemedText>
              <ThemedTextInput
                value={name}
                onChangeText={onChangeName}
                placeholder="John Doe"
              />
            </View>

            <View className="gap-4">
              <ThemedText type="subtitle">Email</ThemedText>
              <ThemedTextInput
                value={email}
                onChangeText={onChangeEmail}
                placeholder="john.doe@gmail.com"
              />
            </View>

            <View className="gap-4">
              <ThemedText type="subtitle">Password</ThemedText>
              <ThemedTextInput
                value={password}
                onChangeText={onChangePassword}
                secureTextEntry={true}
              />
            </View>
          </View>

          <ThemedButton title="Save" onPress={handleSave} />
        </View>
      </Pressable>
    </KeyboardAvoidingView>
  );
}
