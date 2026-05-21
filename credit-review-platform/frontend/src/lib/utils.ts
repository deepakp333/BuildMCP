import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const API_BASE = import.meta.env.VITE_API_URL || "/api";

export function wsUrl(): string {
  if (import.meta.env.VITE_WS_URL) {
    return `${import.meta.env.VITE_WS_URL}/ws/mcp`;
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/mcp`;
}
