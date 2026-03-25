"use client";

import { useRouter } from "next/navigation";
import { OnboardingWizard } from "@/components/onboarding/wizard";

export default function OnboardingPage() {
  const router = useRouter();

  const handleComplete = async (data: {
    platforms: string[];
    riskLevel: string;
    categories: string[];
    automationLevel: string;
  }) => {
    try {
      const { completeOnboarding } = await import("@/lib/api");
      await completeOnboarding(data);
    } catch (err) {
      console.error("Onboarding API failed:", err);
    }
    router.push("/cockpit");
  };

  return <OnboardingWizard onComplete={handleComplete} />;
}
