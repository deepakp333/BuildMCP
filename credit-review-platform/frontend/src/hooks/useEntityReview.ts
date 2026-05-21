import { useMutation, useQuery } from "@tanstack/react-query";
import { getReview, resolveEntity, runReview } from "../lib/api";
import { useReviewStore } from "../store/reviewStore";
import type { EntityType, PrivateReviewResult, PublicReviewResult } from "../types";

export function useResolveEntity(entityType: EntityType | "auto" = "auto") {
  return useMutation({
    mutationFn: (query: string) => resolveEntity(query, entityType),
  });
}

export function useRunReview(entityType: EntityType) {
  const store = useReviewStore();
  return useMutation({
    mutationFn: async () => {
      const entity = store.selectedEntity;
      if (!entity) throw new Error("No entity selected");
      store.clearCommentary();
      store.clearReviews();
      return runReview(entity, entityType);
    },
    onSuccess: (data) => {
      store.setActiveReviewId(data.review_id);
    },
  });
}

export function useReviewPoll(reviewId: string | null, enabled = true) {
  const store = useReviewStore();
  return useQuery({
    queryKey: ["review", reviewId],
    queryFn: () => getReview(reviewId!),
    enabled: !!reviewId && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 1500 : false;
    },
    select: (data) => {
      if (data.result && data.status === "completed") {
        if ("filings" in data.result) {
          store.setPublicReview(data.result as PublicReviewResult);
        } else {
          store.setPrivateReview(data.result as PrivateReviewResult);
        }
      }
      return data;
    },
  });
}
