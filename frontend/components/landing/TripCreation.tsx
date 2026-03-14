import { useEffect, useState } from "react";
import { Alert, Pressable, View } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { ThemedTextInput } from "@/components/ThemedTextInput";
import { ThemedDropdown } from "@/components/ThemedDropdown";
import { apiFetch } from "@/constants/api";
import { BagType, LocationResult, Trip } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedMultiSelect } from "@/components/ThemedMultiSelect";
import { DateSelect } from "@/components/DateSelect";
import { LocationInput } from "@/components/LocationInput";
import { RequiredLabel } from "@/components/RequiredLabel";
import { ThemedButton } from "@/components/ThemedButton";
import { useTheme } from "@/theme/useTheme";
import { ThemedLoading } from "@/components/ThemedLoading";
import { delay } from "@/helpers/delay";
import { ScreenScroll } from "@/components/ScreenScroll";

export function TripCreation({ onContinue }: { onContinue: () => void }) {
  const theme = useTheme();

  const [origin, onChangeOrigin] = useState<LocationResult>({
    city: "",
    state: undefined,
    country: "",
    airport_code: "",
  });
  const [destination, onChangeDestination] = useState<LocationResult>({
    city: "",
    state: undefined,
    country: "",
    airport_code: "",
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

  // DEV MODE ONLY TODO: REMOVE FOR PROD
  const fillDemoData = () => {
    onChangeOrigin({
      city: "New York",
      state: "New York",
      country: "United States",
      airport_code: "JFK",
    });
    onChangeDestination({
      city: "Toronto",
      state: "Ontario",
      country: "Canada",
      airport_code: "YYZ",
    });
    setStartDate("2026-06-01");
    setEndDate("2026-06-06");
    onChangeAirline("Air Canada");
    onChangeBagType(BagType.checked);
  };

  const getDateRangeDisplay = () => {
    if (!startDate && !endDate) {
      return "Select dates";
    }
    if (startDate && !endDate) {
      return startDate;
    }
    return `${startDate} - ${endDate}`;
  };

  const canSave =
    origin.country.trim() !== "" &&
    origin.airport_code.trim().length === 3 &&
    destination.country.trim() !== "" &&
    destination.airport_code.trim().length === 3 &&
    startDate !== "" &&
    endDate !== "" &&
    airline !== "" &&
    bagType !== "";

  async function handleGenerate() {
    try {
      setIsLoading(true);

      const trip: Trip = {
        origin_details: origin,
        destination_details: destination,
        airline,
        start_date: startDate,
        end_date: endDate,
        bag_type: bagType,
        activities: activities.length > 0 ? activities : undefined,
        doing_laundry: laundry,
      };

      await saveToAPI(trip);
      await delay(3000);

      onContinue();
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

  async function saveToAPI(tripInput: Trip): Promise<Trip> {
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
    return result;
  }

  return (
    <ScreenScroll>
      <View className="gap-6">
        <ThemedText type="title">Create your trip</ThemedText>
        <View className="gap-2">
          <RequiredLabel>Origin</RequiredLabel>
          <LocationInput onSelect={onChangeOrigin} />
        </View>

        <View className="gap-2">
          <RequiredLabel>Origin Airport Code</RequiredLabel>
          <ThemedTextInput
            value={origin.airport_code}
            onChangeText={(value) =>
              onChangeOrigin({
                ...origin,
                airport_code: value
                  .toUpperCase()
                  .replace(/[^A-Z]/g, "")
                  .slice(0, 3),
              })
            }
            placeholder="e.g. JFK"
            autoCapitalize="characters"
            maxLength={3}
          />
        </View>

        <View className="gap-2">
          <RequiredLabel>Destination</RequiredLabel>
          <LocationInput onSelect={onChangeDestination} />
        </View>

        <View className="gap-2">
          <RequiredLabel>Destination Airport Code</RequiredLabel>
          <ThemedTextInput
            value={destination.airport_code}
            onChangeText={(value) =>
              onChangeDestination({
                ...destination,
                airport_code: value
                  .toUpperCase()
                  .replace(/[^A-Z]/g, "")
                  .slice(0, 3),
              })
            }
            placeholder="e.g. YYZ"
            autoCapitalize="characters"
            maxLength={3}
          />
        </View>

        <View className="gap-2">
          <RequiredLabel>Trip Dates</RequiredLabel>
          <Pressable onPress={() => setIsCalendarVisible(!isCalendarVisible)}>
            <ThemedTextInput
              value={getDateRangeDisplay()}
              editable={false}
              pointerEvents="none"
              style={{
                color:
                  getDateRangeDisplay() === "Select dates"
                    ? theme.textPlaceholder
                    : theme.text,
              }}
            />
          </Pressable>
          {isCalendarVisible && (
            <View className="gap-2">
              <DateSelect
                startDate={startDate}
                endDate={endDate}
                setStartDate={setStartDate}
                setEndDate={setEndDate}
                onRangeComplete={() => setIsCalendarVisible(false)}
              />
            </View>
          )}
        </View>

        <View className="gap-2">
          <RequiredLabel>Airline</RequiredLabel>
          <ThemedDropdown
            value={airline}
            onChange={(value: string) => onChangeAirline(value)}
            data={airlineOptions}
            placeholder="Select airline"
          />
        </View>

        <View className="gap-2">
          <RequiredLabel>Bag Type</RequiredLabel>
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
          <ThemedText type="subtitle">Activities Planned (Optional)</ThemedText>
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

        <ThemedButton
          onPress={fillDemoData}
          title="Fill demo data"
          variant="outline"
        />
        <ThemedButton
          title="Generate"
          onPress={() => void handleGenerate()}
          disabled={!canSave || isLoading}
          className={canSave && !isLoading ? "opacity-100" : "opacity-50"}
        />
        <ThemedLoading isLoading={isLoading} message="Saving your trip..." />
      </View>
    </ScreenScroll>
  );
}
