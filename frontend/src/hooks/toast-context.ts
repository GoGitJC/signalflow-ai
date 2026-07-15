import type { ReactNode } from "react";
import { createContext, useContext } from "react";

type ToastInput = { title: string; description?: string; variant?: "default" | "danger" };

type ToastContextValue = {
  toast: (input: ToastInput) => void;
};

export const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastSystem");
  return ctx;
}

export type { ToastInput, ToastContextValue, ReactNode };
