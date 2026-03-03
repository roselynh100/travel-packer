import { useState } from "react";
import { Alert, View } from "react-native";
import { useRouter } from "expo-router";

import { ThemedTextInput } from "@/components/ThemedTextInput";
import { ThemedDropdown } from "@/components/ThemedDropdown";
import { apiFetch } from "@/constants/api";
import { Gender, User } from "@/constants/types";
import { useAppContext } from "@/helpers/AppContext";
import { RequiredLabel } from "@/components/RequiredLabel";
import { FormScreenLayout } from "@/components/FormScreenLayout";

export default function UserInfo() {
  const router = useRouter();

  const [name, onChangeName] = useState("");
  const [email, onChangeEmail] = useState("");
  const [password, onChangePassword] = useState("");
  const [age, onChangeAge] = useState("");
  const [gender, onChangeGender] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  const { setUserId } = useAppContext();

  const ageNum = age.trim() === "" ? NaN : parseInt(age, 10);
  const isAgeValid = !Number.isNaN(ageNum) && ageNum > 0;
  const canSave =
    name.trim() !== "" && email.trim() !== "" && isAgeValid && gender !== "";

  async function handleSave() {
    try {
      setIsLoading(true);

      const user: User = {
        name,
        email,
        password,
        age: ageNum,
        gender,
      };

      await saveToAPI(user);
      await new Promise((resolve) => setTimeout(resolve, 5000));

      router.push("/TripInfo");
    } catch (error) {
      console.error("Error creating user:", error);
      Alert.alert(
        "Error",
        error instanceof Error ? error.message : "Failed to create user",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function saveToAPI(userInput: User) {
    const response = await apiFetch("/users/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userInput),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `API error (${response.status}): ${errorText || response.statusText}`,
      );
    }

    const result: User = await response.json();
    console.log("Save success:", result);
    setUserId(result.user_id ?? "No user id saved");
  }

  return (
    <FormScreenLayout
      title="Input your information 🤸"
      onSave={handleSave}
      saveDisabled={!canSave}
      isLoading={isLoading}
      loadingMessage="Saving user information..."
    >
      <View className="gap-2">
        <RequiredLabel>Name</RequiredLabel>
        <ThemedTextInput
          value={name}
          onChangeText={onChangeName}
          placeholder="John Doe"
        />
      </View>

      <View className="gap-2">
        <RequiredLabel>Email</RequiredLabel>
        <ThemedTextInput
          value={email}
          onChangeText={onChangeEmail}
          placeholder="john.doe@gmail.com"
        />
      </View>

      <View className="gap-2">
        <RequiredLabel>Age</RequiredLabel>
        <ThemedTextInput
          value={age}
          onChangeText={onChangeAge}
          keyboardType="numeric"
        />
      </View>

      <View className="gap-2">
        <RequiredLabel>Gender</RequiredLabel>
        <ThemedDropdown
          value={gender}
          onChange={(value: string) => onChangeGender(value)}
          data={Object.entries(Gender).map(([key, value]) => ({
            label: value,
            value: key,
          }))}
          placeholder="Select gender"
        />
      </View>
    </FormScreenLayout>
  );
}
