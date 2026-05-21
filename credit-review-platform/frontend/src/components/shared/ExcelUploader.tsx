import { useCallback, useState } from "react";
import { Upload, Download } from "lucide-react";
import { Button } from "../ui/button";
import { EntityTable } from "./EntityTable";
import { parseExcelClient, useBatchUpload } from "@/hooks/useBatchUpload";
import type { ExcelEntityRow } from "@/types";

export function ExcelUploader({
  onEntitiesParsed,
}: {
  onEntitiesParsed?: (entities: ExcelEntityRow[]) => void;
}) {
  const [entities, setEntities] = useState<ExcelEntityRow[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [dragOver, setDragOver] = useState(false);
  const batchUpload = useBatchUpload();

  const handleFile = useCallback(
    async (file: File) => {
      const parsed = await parseExcelClient(file);
      setEntities(parsed);
      setSelected(new Set(parsed.map((_, i) => i)));
      onEntitiesParsed?.(parsed);
      await batchUpload.mutateAsync(file);
    },
    [batchUpload, onEntitiesParsed]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const toggle = (i: number) => {
    const next = new Set(selected);
    if (next.has(i)) next.delete(i);
    else next.add(i);
    setSelected(next);
  };

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
          dragOver ? "border-blue-500 bg-blue-950/20" : "border-slate-600 bg-slate-900/50"
        }`}
      >
        <Upload className="h-8 w-8 text-slate-500 mb-2" />
        <p className="text-sm text-slate-400 mb-3">Drag & drop Excel batch file (.xlsx)</p>
        <div className="flex gap-2">
          <label>
            <input
              type="file"
              accept=".xlsx,.xls"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
            <Button variant="outline" asChild>
              <span>Choose File</span>
            </Button>
          </label>
          <a href="/template.xlsx" download>
            <Button variant="ghost" type="button">
              <Download className="h-4 w-4 mr-1" />
              Template
            </Button>
          </a>
        </div>
      </div>
      {batchUpload.isSuccess && (
        <p className="text-xs text-green-400">
          Batch uploaded: {batchUpload.data?.batch_id} ({batchUpload.data?.count} entities)
        </p>
      )}
      <EntityTable entities={entities} selected={selected} onToggle={toggle} />
    </div>
  );
}
