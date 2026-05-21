import { useState } from "react";
import { Search } from "lucide-react";
import { Button } from "../ui/button";
import { useResolveEntity } from "@/hooks/useEntityReview";
import { useReviewStore } from "@/store/reviewStore";
import type { EntityType } from "@/types";

export function EntitySearch({ entityType }: { entityType: EntityType }) {
  const [query, setQuery] = useState("");
  const resolve = useResolveEntity(entityType);
  const store = useReviewStore();

  const handleSearch = async () => {
    if (!query.trim()) return;
    const entity = await resolve.mutateAsync(query);
    if (entity) store.setSelectedEntity(entity);
  };

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder={
            entityType === "public"
              ? "Search by name or ticker (e.g. JPM)"
              : "Search by name or FDIC cert number"
          }
          className="w-full rounded-md border border-slate-600 bg-slate-900 py-2 pl-10 pr-4 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
        />
      </div>
      <Button onClick={handleSearch} disabled={resolve.isPending}>
        {resolve.isPending ? "Searching..." : "Resolve"}
      </Button>
    </div>
  );
}
