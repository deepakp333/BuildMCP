import { useMutation } from "@tanstack/react-query";
import * as XLSX from "xlsx";
import { uploadBatch } from "../lib/api";
import { useReviewStore } from "../store/reviewStore";
import type { EntityType, ExcelEntityRow } from "../types";

export function useBatchUpload() {
  const store = useReviewStore();
  return useMutation({
    mutationFn: (file: File) => uploadBatch(file),
    onSuccess: (data) => {
      store.setBatch(data.batch_id, data.entities);
    },
  });
}

export function parseExcelClient(file: File): Promise<ExcelEntityRow[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: "array" });
        const sheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json<Record<string, string>>(sheet);
        const entities: ExcelEntityRow[] = rows
          .map((row) => {
            const name =
              row.name || row.Name || row.entity_name || row.Entity_Name || "";
            if (!name) return null;
            const typeRaw = row.entity_type || row.type || row.Type || "private";
            const entity_type: EntityType = String(typeRaw)
              .toLowerCase()
              .startsWith("pub")
              ? "public"
              : "private";
            return {
              name: String(name),
              entity_type,
              ticker: row.ticker || row.Ticker || null,
              cert_number: row.cert || row.cert_number || null,
              notes: row.notes || null,
            };
          })
          .filter(Boolean) as ExcelEntityRow[];
        resolve(entities);
      } catch (err) {
        reject(err);
      }
    };
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}
