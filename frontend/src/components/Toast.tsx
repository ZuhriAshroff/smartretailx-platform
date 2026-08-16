import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface ToastItem {
  id: number;
  message: string;
  kind: "error" | "success";
}

interface ToastContextValue {
  showError: (message: string) => void;
  showSuccess: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((message: string, kind: "error" | "success") => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, message, kind }]);
    setTimeout(() => dismiss(id), 4000);
  }, [dismiss]);

  const value = useMemo(
    () => ({
      showError: (message: string) => push(message, "error"),
      showSuccess: (message: string) => push(message, "success"),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => {
          const Icon = t.kind === "error" ? AlertCircle : CheckCircle2;
          return (
            <div
              key={t.id}
              className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-medium text-white shadow-lg ${
                t.kind === "error" ? "bg-red-600" : "bg-emerald-600"
              }`}
            >
              <Icon size={16} />
              {t.message}
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a ToastProvider");
  return ctx;
}
