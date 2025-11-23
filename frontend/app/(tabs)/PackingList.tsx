import { useState } from "react";
import { SectionList, View } from "react-native";
import { Checkbox } from "expo-checkbox";

import { ThemedText } from "@/components/ThemedText";

export default function PackingList() {
  const [checkedItems, setCheckedItems] = useState<Set<string>>(new Set());
  const DATA = [
    {
      title: "Clothes",
      data: [
        "Shirt",
        "Pants",
        "Shorts",
        "Dress",
        "Jacket",
        "Socks",
        "Underwear",
      ],
    },
    {
      title: "Toiletries",
      data: ["Toothbrush", "Toothpaste", "Retainer", "Contacts", "Deodorant"],
    },
    {
      title: "Electronics",
      data: ["Laptop", "Laptop charger", "Headphones", "Power Bank"],
    },
    {
      title: "Miscellaneous",
      data: ["Wallet", "Passport", "Glasses"],
    },
  ];

  return (
    <View className="flex flex-col gap-4 p-12">
      <ThemedText type="title">Packing List</ThemedText>
      <SectionList
        sections={DATA}
        keyExtractor={(item, index) => item + index}
        renderItem={({ item, section }) => {
          const key = `${section.title}-${item}`;
          return (
            <View className="flex flex-row gap-2 items-center">
              <Checkbox
                value={checkedItems.has(key)}
                onValueChange={() => {
                  setCheckedItems((prev) => {
                    const next = new Set(prev);
                    if (next.has(key)) next.delete(key);
                    else next.add(key);
                    return next;
                  });
                }}
              />
              <ThemedText>{item}</ThemedText>
            </View>
          );
        }}
        renderSectionHeader={({ section: { title } }) => (
          <ThemedText type="subtitle" className="mt-4 mb-2">
            {title}
          </ThemedText>
        )}
      />
    </View>
  );
}
