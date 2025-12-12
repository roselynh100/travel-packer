import { useState } from "react";
import {
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  View,
} from "react-native";
import { useRouter } from "expo-router";

import { ThemedText } from "@/components/ThemedText";
import { ThemedTextInput } from "@/components/ThemedTextInput";
import { ThemedButton } from "@/components/ThemedButton";
import { API_BASE_URL } from "@/constants/api";
import { Gender, User } from "@/constants/types";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedDropdown } from "@/components/ThemedDropdown";
import { ThemedLoading } from "@/components/ThemedLoading";

export default function HomeScreen() {
  const router = useRouter();

  const [name, onChangeName] = useState("");
  const [email, onChangeEmail] = useState("");
  const [password, onChangePassword] = useState("");
  const [age, onChangeAge] = useState("");
  const [gender, onChangeGender] = useState<Gender>(Gender.Other);
  const [isLoading, setIsLoading] = useState(false);

  const { setUserId } = useAppContext();

  async function handleSave() {
    try {
      setIsLoading(true);

      // TODO: Fix stuff about password
      const user: User = {
        name,
        email,
        password,
        age: parseInt(age),
        gender,
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
      const response = await fetch(`${API_BASE_URL}/users/`, {
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
            <ThemedText type="title">Input your information 🤸</ThemedText>
            <View className="gap-2">
              <ThemedText type="subtitle">Name</ThemedText>
              <ThemedTextInput
                value={name}
                onChangeText={onChangeName}
                placeholder="John Doe"
              />
            </View>

            <View className="gap-2">
              <ThemedText type="subtitle">Email</ThemedText>
              <ThemedTextInput
                value={email}
                onChangeText={onChangeEmail}
                placeholder="john.doe@gmail.com"
              />
            </View>

            {/* <View className="gap-2">
                <ThemedText type="subtitle">Password</ThemedText>
                <ThemedTextInput
                  value={password}
                  onChangeText={onChangePassword}
                  secureTextEntry={true}
                />
              </View> */}

            <View className="gap-2">
              <ThemedText type="subtitle">Age</ThemedText>
              <ThemedTextInput
                value={age}
                onChangeText={onChangeAge}
                keyboardType="numeric"
              />
            </View>

            <View className="gap-2">
              <ThemedText type="subtitle">Gender</ThemedText>
              <ThemedDropdown
                value={gender}
                onChange={onChangeGender}
                options={Object.values(Gender)}
              />
            </View>
          </View>

          <ThemedButton title="Save" onPress={handleSave} />
          <ThemedLoading
            isLoading={isLoading}
            message="Saving user information..."
          />
        </ScrollView>
      </Pressable>
    </KeyboardAvoidingView>
  );
}
