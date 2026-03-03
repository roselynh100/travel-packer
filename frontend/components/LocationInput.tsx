import { useEffect, useState, useRef } from "react";
import { View, Text, Pressable, ScrollView } from "react-native";
import { LocationResult } from "@/constants/types";
import { ThemedTextInput } from "@/components/ThemedTextInput";
import { ThemedText } from "@/components/ThemedText";

export function LocationInput({
  onSelect,
}: {
  onSelect: (location: LocationResult) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const isSelectingRef = useRef(false);

  useEffect(() => {
    // Skip search if user just selected something
    if (isSelectingRef.current) {
      isSelectingRef.current = false;
      return;
    }

    // Clear loading state immediately if query is too short
    if (query.length < 2) {
      setResults([]);
      setLoading(false);
      return;
    }

    // Show loading only when we have a valid query
    setLoading(true);

    const timeout = setTimeout(async () => {
      try {
        const data = await searchLocations(query);
        setResults(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }, 2000); // debounce

    return () => {
      clearTimeout(timeout);
      setLoading(false);
    };
  }, [query]);

  async function searchLocations(query: string) {
    if (!query || query.length < 2) return [];

    const url =
      "https://nominatim.openstreetmap.org/search?" +
      new URLSearchParams({
        q: query,
        format: "json",
        addressdetails: "1",
        limit: "10",
        featuretype: "city",
      });

    const res = await fetch(url, {
      headers: {
        "User-Agent": "Packulus/1.0",
      },
    });

    const data = await res.json();

    // Filter to only include actual cities/towns/villages
    const filtered = data.filter((item: any) => {
      const address = item.address || {};
      const hasCity = getCity(address);
      const hasCountry = address.country;
      // Exclude weird regions/areas that aren't actual places
      const isNotRegion = !item.type.includes("region");
      return hasCity && hasCountry && isNotRegion;
    });

    // Remove duplicates
    const seen = new Set<string>();
    const unique = filtered.filter((item: any) => {
      const display = formatLocationDisplay(item);
      if (seen.has(display)) {
        return false;
      }
      seen.add(display);
      return true;
    });

    return unique.slice(0, 5); // Limit to 5
  }

  function getCity(address: any) {
    return (
      address.city ||
      address.town ||
      address.village ||
      address.hamlet ||
      address.municipality ||
      undefined
    );
  }

  function parseLocation(item: any) {
    const address = item.address || {};
    const city = getCity(address) || "";
    const state = address.state || address.province || undefined;
    const country = address.country || "";

    return { city, state, country } as LocationResult;
  }

  function formatLocationDisplay(item: any): string {
    const { city, state, country } = parseLocation(item);
    return state ? `${city}, ${state}, ${country}` : `${city}, ${country}`;
  }

  function handleSelect(item: any) {
    const location = parseLocation(item);
    const displayText = formatLocationDisplay(item);

    // Mark that we're selecting to prevent search from triggering
    isSelectingRef.current = true;
    setQuery(displayText);
    setResults([]);
    onSelect(location);
  }

  return (
    <View>
      <ThemedTextInput
        value={query}
        onChangeText={setQuery}
        placeholder="City, Country"
      />

      {results.length > 0 && (
        <View className="border border-gray-200 rounded mt-1 bg-white max-h-64">
          <ScrollView>
            {results.map((item) => (
              <Pressable
                key={item.place_id.toString()}
                onPress={() => handleSelect(item)}
                className="p-3 border-b border-gray-100"
              >
                <Text>{formatLocationDisplay(item)}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      )}

      {loading && (
        <ThemedText className="text-sm mt-2 text-gray-500">
          Searching...
        </ThemedText>
      )}
    </View>
  );
}
