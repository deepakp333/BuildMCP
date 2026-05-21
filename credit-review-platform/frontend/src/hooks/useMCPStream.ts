import { useCallback, useRef, useState } from "react";
import { wsUrl } from "../lib/utils";
import { useReviewStore } from "../store/reviewStore";
import type { EntityType, PrivateReviewResult, PublicReviewResult, ResolvedEntity } from "../types";

export function useMCPStream() {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const store = useReviewStore();

  const runReviewWithStream = useCallback(
    (entity: ResolvedEntity, entityType: EntityType) => {
      store.clearCommentary();
      store.setIsStreaming(true);

      const ws = new WebSocket(wsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        ws.send(
          JSON.stringify({
            action: "run_review",
            entity,
            entity_type: entityType,
          })
        );
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "commentary" && msg.chunk) {
          store.appendCommentary(msg.chunk);
        }
        if (msg.type === "complete") {
          store.setIsStreaming(false);
          if (msg.review_id) store.setActiveReviewId(msg.review_id);
          try {
            const result = JSON.parse(msg.chunk);
            if (result && result.entity) {
              if ("filings" in result) {
                store.setPublicReview(result as PublicReviewResult);
              } else {
                store.setPrivateReview(result as PrivateReviewResult);
              }
            }
          } catch {
            /* polling will pick up result */
          }
          ws.close();
        }
        if (msg.type === "error") {
          store.setIsStreaming(false);
          store.appendCommentary(`\nError: ${msg.error || msg.chunk}`);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        store.setIsStreaming(false);
      };

      ws.onerror = () => {
        store.setIsStreaming(false);
        setConnected(false);
      };
    },
    [store]
  );

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    setConnected(false);
  }, []);

  return { runReviewWithStream, disconnect, connected };
}
