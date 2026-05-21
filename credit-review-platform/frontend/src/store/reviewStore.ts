import { create } from "zustand";
import type {
  EntityType,
  ExcelEntityRow,
  PrivateReviewResult,
  PublicReviewResult,
  ResolvedEntity,
} from "../types";

interface ReviewState {
  selectedEntity: ResolvedEntity | null;
  publicReview: PublicReviewResult | null;
  privateReview: PrivateReviewResult | null;
  activeReviewId: string | null;
  commentary: string;
  isStreaming: boolean;
  batchEntities: ExcelEntityRow[];
  batchId: string | null;
  setSelectedEntity: (e: ResolvedEntity | null) => void;
  setPublicReview: (r: PublicReviewResult | null) => void;
  setPrivateReview: (r: PrivateReviewResult | null) => void;
  setActiveReviewId: (id: string | null) => void;
  appendCommentary: (chunk: string) => void;
  clearCommentary: () => void;
  setIsStreaming: (v: boolean) => void;
  setBatch: (id: string, entities: ExcelEntityRow[]) => void;
  clearReviews: () => void;
}

export const useReviewStore = create<ReviewState>((set) => ({
  selectedEntity: null,
  publicReview: null,
  privateReview: null,
  activeReviewId: null,
  commentary: "",
  isStreaming: false,
  batchEntities: [],
  batchId: null,
  setSelectedEntity: (e) => set({ selectedEntity: e }),
  setPublicReview: (r) => set({ publicReview: r }),
  setPrivateReview: (r) => set({ privateReview: r }),
  setActiveReviewId: (id) => set({ activeReviewId: id }),
  appendCommentary: (chunk) => set((s) => ({ commentary: s.commentary + chunk })),
  clearCommentary: () => set({ commentary: "" }),
  setIsStreaming: (v) => set({ isStreaming: v }),
  setBatch: (id, entities) => set({ batchId: id, batchEntities: entities }),
  clearReviews: () =>
    set({
      publicReview: null,
      privateReview: null,
      activeReviewId: null,
      commentary: "",
    }),
}));

export type { EntityType };
