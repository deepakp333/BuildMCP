import { useMutation } from "@tanstack/react-query";
import { uploadBatch } from "../lib/api";
import { useReviewStore } from "../store/reviewStore";

export function useBatchUpload() {
  const store = useReviewStore();
  return useMutation({
    mutationFn: (file: File) => uploadBatch(file),
    onSuccess: (data) => {
      store.setBatch(data.batch_id, data.entities);
    },
  });
}
