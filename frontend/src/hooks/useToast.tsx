import { useCallback, useMemo, useState, type ReactNode } from "react";
import {
  Toast,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast";
import { ToastContext, type ToastInput } from "@/hooks/toast-context";

export function ToastSystem({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Array<ToastInput & { id: string }>>([]);

  const toast = useCallback((input: ToastInput) => {
    const id = crypto.randomUUID();
    setItems((current) => [...current, { ...input, id }]);
    window.setTimeout(() => {
      setItems((current) => current.filter((item) => item.id !== id));
    }, 3200);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      <ToastProvider swipeDirection="right">
        {children}
        {items.map((item) => (
          <Toast key={item.id} open variant={item.variant}>
            <ToastTitle>{item.title}</ToastTitle>
            {item.description ? <ToastDescription>{item.description}</ToastDescription> : null}
          </Toast>
        ))}
        <ToastViewport />
      </ToastProvider>
    </ToastContext.Provider>
  );
}
