import { API_BASE } from "./utils";
import type {
  EntityType,
  ExcelEntityRow,
  PrivateReviewResult,
  PublicReviewResult,
  ResolvedEntity,
} from "../types";

export async function resolveEntity(
  query: string,
  entityType: EntityType | "auto" = "auto"
): Promise<ResolvedEntity | null> {
  const res = await fetch(`${API_BASE}/entities/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, entity_type: entityType }),
  });
  if (!res.ok) throw new Error("Failed to resolve entity");
  const data = await res.json();
  return data.entity;
}

export async function runReview(
  entity: ResolvedEntity,
  entityType: EntityType
): Promise<{ review_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/review/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity, entity_type: entityType }),
  });
  if (!res.ok) throw new Error("Failed to start review");
  return res.json();
}

export async function getReview(reviewId: string): Promise<{
  review_id: string;
  status: string;
  result: PublicReviewResult | PrivateReviewResult | null;
  error?: string;
}> {
  const res = await fetch(`${API_BASE}/review/${reviewId}`);
  if (!res.ok) throw new Error("Review not found");
  return res.json();
}

export async function uploadBatch(file: File): Promise<{
  batch_id: string;
  entities: ExcelEntityRow[];
  count: number;
}> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/batch/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Batch upload failed");
  return res.json();
}

export async function getBatch(batchId: string) {
  const res = await fetch(`${API_BASE}/batch/${batchId}`);
  if (!res.ok) throw new Error("Batch not found");
  return res.json();
}
