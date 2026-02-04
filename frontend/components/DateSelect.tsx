import { useEffect, useState } from "react";
import { View, Pressable } from "react-native";

import {
  Calendar,
  toDateId,
  useDateRange,
} from "@marceloterreiro/flash-calendar";
import { ThemedText } from "@/components/ThemedText";

type DateSelectProps = {
  startDate: string;
  endDate: string;
  setStartDate: (date: string) => void;
  setEndDate: (date: string) => void;
};

export const DateSelect = ({
  startDate,
  endDate,
  setStartDate,
  setEndDate,
}: DateSelectProps) => {
  const [currentMonth, setCurrentMonth] = useState(toDateId(new Date()));

  const today = toDateId(new Date());

  // Limit: 2 years from today
  const MAX_DATE = toDateId(
    new Date(new Date().setFullYear(new Date().getFullYear() + 2)),
  );

  const { calendarActiveDateRanges, onCalendarDayPress, dateRange } =
    useDateRange({
      startId: startDate || undefined,
      endId: endDate || undefined,
    });

  useEffect(() => {
    if (dateRange.startId) {
      setStartDate(dateRange.startId);
    }
    if (dateRange.endId) {
      setEndDate(dateRange.endId);
    }
  }, [dateRange]);

  const goToPreviousMonth = () => {
    const date = new Date(currentMonth);
    date.setMonth(date.getMonth() - 1);
    const newMonth = toDateId(date);
    if (newMonth >= today.substring(0, 7)) {
      setCurrentMonth(newMonth);
    }
  };

  const goToNextMonth = () => {
    const date = new Date(currentMonth);
    date.setMonth(date.getMonth() + 1);
    const newMonth = toDateId(date);
    if (newMonth <= MAX_DATE) {
      setCurrentMonth(newMonth);
    }
  };

  const canGoPrevious = currentMonth > today.substring(0, 7);
  const canGoNext = currentMonth < MAX_DATE.substring(0, 7);
  return (
    <>
      <View className="flex-row justify-between items-center px-4">
        <Pressable onPress={goToPreviousMonth} disabled={!canGoPrevious}>
          <ThemedText
            style={{ opacity: canGoPrevious ? 1 : 0.3 }}
            type="subtitle"
          >
            ← Prev
          </ThemedText>
        </Pressable>
        <ThemedText type="subtitle">
          {new Date(currentMonth).toLocaleDateString("en-US", {
            month: "long",
            year: "numeric",
          })}
        </ThemedText>
        <Pressable onPress={goToNextMonth} disabled={!canGoNext}>
          <ThemedText style={{ opacity: canGoNext ? 1 : 0.3 }} type="subtitle">
            Next →
          </ThemedText>
        </Pressable>
      </View>
      <Calendar
        calendarActiveDateRanges={calendarActiveDateRanges}
        calendarMonthId={currentMonth}
        calendarMinDateId={today}
        calendarMaxDateId={MAX_DATE}
        onCalendarDayPress={onCalendarDayPress}
      />
    </>
  );
};
