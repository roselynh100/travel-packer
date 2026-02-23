import { useEffect, useState } from "react";
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
import { ThemedDropdown } from "@/components/ThemedDropdown";
import { apiFetch } from "@/constants/api";
import { BagType, LocationResult, Trip } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedLoading } from "@/components/ThemedLoading";
import { ThemedMultiSelect } from "@/components/ThemedMultiSelect";
import { DateSelect } from "@/components/DateSelect";
import { LocationInput } from "@/components/LocationInput";

export default function TripInfo() {
  const router = useRouter();

  const [destination, onChangeDestination] = useState<LocationResult>({
    city: "",
    state: undefined,
    country: "",
  });
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [isCalendarVisible, setIsCalendarVisible] = useState(false);
  const [laundry, onChangeLaundry] = useState(false);
  const [airline, onChangeAirline] = useState<string>("");
  const [airlineOptions, setAirlineOptions] = useState<
    { label: string; value: string }[]
  >([]);
  const [bagType, onChangeBagType] = useState<string>("");
  const [activities, onChangeActivities] = useState<string[]>([]);
  const [activityOptions, setActivityOptions] = useState<
    { label: string; value: string }[]
  >([]);
  const [isLoading, setIsLoading] = useState(false);

  const { userId, setTripId } = useAppContext();

  useEffect(() => {
    const fetchAirlines = async () => {
      try {
        const response = await apiFetch("/trips/airlines");

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        const airlinesList: string[] = await response.json();
        const formattedAirlines = airlinesList.map((airline) => ({
          label: airline,
          value: airline,
        }));

        setAirlineOptions(formattedAirlines);
        console.log("Fetched airlines:", formattedAirlines);
      } catch (error) {
        console.error("Error fetching airlines:", error);
      }
    };

    const fetchActivities = async () => {
      try {
        const response = await apiFetch("/trips/activities");

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        const activitiesList: string[] = await response.json();
        const formattedActivities = activitiesList.map((activity) => ({
          label: activity,
          value: activity,
        }));

        setActivityOptions(formattedActivities);
        console.log("Fetched activities:", formattedActivities);
      } catch (error) {
        console.error("Error fetching activities:", error);
      }
    };

    fetchAirlines();
    fetchActivities();
  }, []);

  const getDateRangeDisplay = () => {
    if (!startDate && !endDate) {
      return "Select dates";
    }
    if (startDate && !endDate) {
      return startDate;
    }
    return `${startDate} - ${endDate}`;
  };

  async function handleSave() {
    try {
      setIsLoading(true);

      const trip: Trip = {
        destination_details: destination,
        airline,
        start_date: startDate,
        end_date: endDate,
        bag_type: bagType,
        activities: activities.length > 0 ? activities : undefined,
        doing_laundry: laundry,
      };

      await saveToAPI(trip);
      await new Promise((resolve) => setTimeout(resolve, 5000));

      router.push("/PackingList");
    } catch (error) {
      console.error("Error saving trip details:", error);
      Alert.alert(
        "Error",
        error instanceof Error ? error.message : "Failed to save trip details",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function saveToAPI(tripInput: Trip) {
    try {
      const url = userId ? `/trips/?user_id=${userId}` : "/trips/";

      const response = await apiFetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tripInput),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API error (${response.status}): ${errorText || response.statusText}`,
        );
      }

      const result: Trip = await response.json();
      console.log("Save success:", result);
      setTripId(result.trip_id ?? "No trip id saved");
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
            <ThemedText type="title">Input your trip details 🌴</ThemedText>
            <View className="gap-2">
              <ThemedText type="subtitle">Destination</ThemedText>
              <LocationInput onSelect={onChangeDestination} />
            </View>

            <View className="gap-2">
              <ThemedText type="subtitle">Trip Dates</ThemedText>
              <Pressable
                onPress={() => setIsCalendarVisible(!isCalendarVisible)}
              >
                <ThemedTextInput
                  value={getDateRangeDisplay()}
                  editable={false}
                  pointerEvents="none"
                />
              </Pressable>
              {isCalendarVisible && (
                <View className="gap-2">
                  <DateSelect
                    startDate={startDate}
                    endDate={endDate}
                    setStartDate={setStartDate}
                    setEndDate={setEndDate}
                  />
                </View>
              )}
            </View>

            <View className="gap-2">
              <ThemedText type="subtitle">Airline</ThemedText>
              <ThemedDropdown
                value={airline}
                onChange={(value: string) => onChangeAirline(value)}
                data={airlineOptions}
                placeholder="Select airline"
              />
            </View>

            <View className="gap-2">
              <ThemedText type="subtitle">Bag Type</ThemedText>
              <ThemedDropdown
                value={bagType}
                onChange={(value: string) => onChangeBagType(value)}
                data={Object.values(BagType).map((value) => ({
                  label: value,
                  value: value,
                }))}
                placeholder="Select bag type"
              />
            </View>

            <View className="gap-2">
              <ThemedText type="subtitle">
                Activities Planned (Optional)
              </ThemedText>
              <ThemedMultiSelect
                data={activityOptions}
                value={activities}
                onChange={onChangeActivities}
                placeholder="Search and select activities"
                searchPlaceholder="Search activities..."
              />
            </View>

            <ThemedCheckbox
              label="I am planning to do laundry"
              value={laundry}
              onValueChange={onChangeLaundry}
              size="medium"
            />
          </View>
        </ScrollView>
        <ThemedButton
          title="Save"
          onPress={handleSave}
          className={Platform.OS === "web" ? "mx-12 mb-12" : "mx-6 mb-6"}
        />
        <ThemedLoading isLoading={isLoading} message="Saving your trip..." />
      </Pressable>
    </KeyboardAvoidingView>
  );
}
