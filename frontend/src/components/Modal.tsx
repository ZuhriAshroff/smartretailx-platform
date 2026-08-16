import { useEffect } from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

export function Modal({
  open,
  onClose,
  title,
  icon,
  children,
  maxWidth = "max-w-lg",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  maxWidth?: string;
}) {
  useEffect(() => {
    if (!open) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-neutral-900/30 backdrop-blur-sm" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`relative w-full ${maxWidth} rounded-2xl border border-white/60 bg-white/80 p-5 shadow-2xl shadow-neutral-900/10 backdrop-blur-2xl`}
      >
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            {icon}
            <h2 className="font-display text-base font-semibold text-neutral-900">{title}</h2>
          </div>
          <button
            onClick={onClose}
            title="Close"
            className="flex h-7 w-7 items-center justify-center rounded-lg text-neutral-500 hover:bg-neutral-900/8 hover:text-neutral-900"
          >
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
