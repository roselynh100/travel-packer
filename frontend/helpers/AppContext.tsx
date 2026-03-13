import { ItemWithPackingRecommendation } from "@/constants/types";
import { createContext, useContext, useEffect, useState } from "react";

type AppContextType = {
  userId: string;
  tripId: string | null;
  setTripId: (v: string | null) => void;
  currentItem: ItemWithPackingRecommendation | null;
  setCurrentItem: (
    v:
      | ItemWithPackingRecommendation
      | null
      | ((
          prev: ItemWithPackingRecommendation | null,
        ) => ItemWithPackingRecommendation | null),
  ) => void;
  setUserId: (v: string) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const [userId, setUserId] = useState("");
  const [tripId, setTripId] = useState<string | null>(null);
  const [currentItem, setCurrentItem] =
    useState<ItemWithPackingRecommendation | null>(null);

  // New trip = fresh app: no currently scanned item
  useEffect(() => {
    setCurrentItem(null);
  }, [tripId]);

  return (
    <AppContext.Provider
      value={{
        userId,
        tripId,
        setUserId,
        setTripId,
        currentItem,
        setCurrentItem,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used inside <AppProvider>");
  return ctx;
};
