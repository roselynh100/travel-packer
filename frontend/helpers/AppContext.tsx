import { ItemWithPackingRecommendation } from "@/constants/types";
import { createContext, useContext, useState } from "react";

type AppContextType = {
  userId: string;
  tripId: string;
  setTripId: (v: string) => void;
  currentItem: ItemWithPackingRecommendation | null;
  setCurrentItem: (v: ItemWithPackingRecommendation | null) => void;
  setUserId: (v: string) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const [userId, setUserId] = useState("");
  const [tripId, setTripId] = useState("");
  const [currentItem, setCurrentItem] =
    useState<ItemWithPackingRecommendation | null>(null);

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
