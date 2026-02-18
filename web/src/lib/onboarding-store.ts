import { create } from "zustand";

export interface ShadowVectorAnswers {
  attachmentStyle: "secure" | "anxious" | "avoidant" | "fearful";
  valueRanking: string[];
  fearArchitecture: string[];
  entropyTolerance: number;
  linguisticSignature: string[];
  communicationStyle: { directness: number; expressiveness: number };
  selfTransparency: number;
  relationshipHistory: string;
}

interface OnboardingStore {
  currentStep: number;
  answers: Partial<ShadowVectorAnswers>;
  setAnswer: <K extends keyof ShadowVectorAnswers>(
    key: K,
    value: ShadowVectorAnswers[K]
  ) => void;
  nextStep: () => void;
  prevStep: () => void;
  isComplete: boolean;
}

export const useOnboardingStore = create<OnboardingStore>((set) => ({
  currentStep: 0,
  answers: {},
  isComplete: false,

  setAnswer: (key, value) =>
    set((state) => ({
      answers: { ...state.answers, [key]: value },
    })),

  nextStep: () =>
    set((state) => {
      const next = state.currentStep + 1;
      return {
        currentStep: next,
        isComplete: next > 7,
      };
    }),

  prevStep: () =>
    set((state) => ({
      currentStep: Math.max(0, state.currentStep - 1),
    })),
}));
