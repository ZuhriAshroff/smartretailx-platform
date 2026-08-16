import { AlertTriangle } from "lucide-react";
import { Modal } from "./Modal";

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  danger = false,
  loading = false,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  danger?: boolean;
  loading?: boolean;
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      maxWidth="max-w-sm"
      icon={
        <div
          className={`flex h-8 w-8 items-center justify-center rounded-lg ${
            danger ? "bg-red-100 text-red-600" : "bg-neutral-900/8 text-neutral-700"
          }`}
        >
          <AlertTriangle size={16} />
        </div>
      }
    >
      <p className="mb-5 text-sm text-neutral-600">{description}</p>
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="rounded-xl border border-white/60 bg-white/40 px-4 py-2 text-sm font-medium text-neutral-600 backdrop-blur-sm hover:bg-white/70"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={onConfirm}
          className={`rounded-xl px-4 py-2 font-display text-sm font-semibold text-white shadow-md transition-colors disabled:opacity-50 ${
            danger
              ? "bg-red-600 shadow-red-600/20 hover:bg-red-700"
              : "bg-neutral-800 shadow-neutral-900/10 hover:bg-neutral-700"
          }`}
        >
          {loading ? "Working..." : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
