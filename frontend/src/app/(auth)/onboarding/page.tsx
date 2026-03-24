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
    // TODO: POST to /api/onboarding with data
    // For now, just redirect to cockpit after a brief delay
    await new Promise((r) => setTimeout(r, 1500));
    router.push("/cockpit");
  };

  return <OnboardingWizard onComplete={handleComplete} />;
}
