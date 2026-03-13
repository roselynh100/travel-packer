import { useCallback, useState } from "react";
import { useRouter } from "expo-router";
import { TripCreation, Success, Welcome } from "@/components/landing";
import { useFocusEffect } from "@react-navigation/native";

type LandingStep = "welcome" | "creation" | "success";

export default function Landing() {
  const router = useRouter();
  const [step, setStep] = useState<LandingStep>("welcome");

  // Reset to welcome screen when user leaves the page and comes back
  useFocusEffect(
    useCallback(() => {
      return () => setStep("welcome");
    }, []),
  );

  return (
    <>
      {step === "welcome" && <Welcome onContinue={() => setStep("creation")} />}

      {step === "creation" && (
        <TripCreation onContinue={() => setStep("success")} />
      )}

      {step === "success" && (
        <Success onContinue={() => router.push("/Trips")} />
      )}
    </>
  );
}
