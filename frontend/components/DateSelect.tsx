import { useEffect, useMemo, useRef, useState } from "react";
import { View, Pressable } from "react-native";

import {
  Calendar,
  toDateId,
  useDateRange,
  type CalendarTheme,
} from "@marceloterreiro/flash-calendar";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";

type DateSelectProps = {
  startDate: string;
  endDate: string;
  setStartDate: (date: string) => void;
  setEndDate: (date: string) => void;
  onRangeComplete?: () => void;
};

export const DateSelect = ({
  startDate,
  endDate,
  setStartDate,
  setEndDate,
  onRangeComplete,
}: DateSelectProps) => {
  const theme = useTheme();
  const [currentMonth, setCurrentMonth] = useState(toDateId(new Date()));

  const today = toDateId(new Date());

  const calendarTheme: CalendarTheme = useMemo(
    () => ({
      rowMonth: {
        container: {
          height: 0,
          overflow: "hidden",
        },
      },
      itemDayContainer: {
        activeDayFiller: {
          backgroundColor: theme.primary,
        },
      },
      itemDay: {
        active: () => ({
          container: {
            backgroundColor: theme.primary,
          },
          content: {
            color: "#ffffff",
          },
        }),
      },
    }),
    [theme.primary],
  );

  // Limit: 2 years from today
  const MAX_DATE = toDateId(
    new Date(new Date().setFullYear(new Date().getFullYear() + 2)),
  );

  const { calendarActiveDateRanges, onCalendarDayPress, dateRange } =
    useDateRange({
      startId: startDate || undefined,
      endId: endDate || undefined,
    });

  const prevRangeRef = useRef({
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
    // Make sure we only run onRangeComplete when the end date is selected for the first time
    // Not when we open the calendar with two dates already selected
    const hadEndBefore = !!prevRangeRef.current.endId;
    const hasEndNow = !!dateRange.endId;
    if (dateRange.startId && hasEndNow && !hadEndBefore) {
      onRangeComplete?.();
    }
    prevRangeRef.current = {
      startId: dateRange.startId,
      endId: dateRange.endId,
    };
  }, [dateRange, onRangeComplete, setStartDate, setEndDate]);

  const goToPreviousMonth = () => {
    const date = new Date(currentMonth);
    date.setMonth(date.getMonth() - 1);
    const newMonth = toDateId(date);
    if (newMonth >= today) {
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

  const canGoPrevious = currentMonth.substring(0, 7) > today.substring(0, 7);
  const canGoNext = currentMonth.substring(0, 7) < MAX_DATE.substring(0, 7);

  return (
    <>
      <View className="flex-row justify-between items-center px-4">
        <Pressable onPress={goToPreviousMonth} disabled={!canGoPrevious}>
          <ThemedText style={{ opacity: canGoPrevious ? 1 : 0.3 }}>
            ← Prev
          </ThemedText>
        </Pressable>
        <ThemedText>
          {new Date(currentMonth).toLocaleDateString("en-US", {
            month: "long",
            year: "numeric",
          })}
        </ThemedText>
        <Pressable onPress={goToNextMonth} disabled={!canGoNext}>
          <ThemedText style={{ opacity: canGoNext ? 1 : 0.3 }}>
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
        theme={calendarTheme}
      />
    </>
  );
};
