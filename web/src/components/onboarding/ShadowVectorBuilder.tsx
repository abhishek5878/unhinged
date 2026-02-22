"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOnboardingStore } from "@/lib/onboarding-store";
import { Step1 } from "./steps/Step1";
import { Step2 } from "./steps/Step2";
import { Step3 } from "./steps/Step3";
import { Step4 } from "./steps/Step4";
import { Step5 } from "./steps/Step5";
import { Step6 } from "./steps/Step6";
import { Step7 } from "./steps/Step7";
import { Step8 } from "./steps/Step8";
import { CompletionScreen } from "./CompletionScreen";

const steps = [Step1, Step2, Step3, Step4, Step5, Step6, Step7, Step8];
// Exit animation duration in ms — counter lags by this so it matches visible content
const EXIT_MS = 360;

export function ShadowVectorBuilder() {
  const { currentStep, isComplete, prevStep } = useOnboardingStore();
  // displayStep lags behind currentStep so the counter matches the content
  // that's actually visible (exit animation takes EXIT_MS ms)
  const [displayStep, setDisplayStep] = useState(currentStep);

  useEffect(() => {
    const t = setTimeout(() => setDisplayStep(currentStep), EXIT_MS);
    return () => clearTimeout(t);
  }, [currentStep]);

  if (isComplete) {
    return <CompletionScreen />;
  }

  const StepComponent = steps[currentStep];

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-[#020408]">
      {/* Progress bar */}
      <div className="fixed top-0 left-0 right-0 z-50 h-[2px] bg-[#162638]">
        <motion.div
          className="h-full bg-[#00c8ff]"
          animate={{ width: `${((displayStep + 1) / 8) * 100}%` }}
          transition={{ duration: 0.4, ease: "easeInOut" }}
        />
      </div>

      {/* Back button + step counter */}
      <div className="fixed top-4 left-4 z-50 flex items-center gap-3">
        {displayStep > 0 && (
          <button
            onClick={prevStep}
            className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/30 hover:text-[#e8f4ff]/70 transition-colors"
          >
            ← back
          </button>
        )}
        <span className="font-[family-name:var(--font-space-mono)] text-xs text-[#e8f4ff]/20">
          {displayStep + 1} / 8
        </span>
      </div>

      {/* mode="wait" ensures only one step is mounted at a time — the old
          step fully exits before the new one enters, making duplicate
          question display impossible regardless of timing */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 60 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -60 }}
          transition={{ duration: 0.25, ease: "easeInOut" }}
          className="absolute inset-0 flex items-center justify-center px-4 pt-12"
        >
          <StepComponent />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
