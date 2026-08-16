import { CheckCircle2, Clock, PackageCheck, Truck, XCircle } from "lucide-react";

const META: Record<string, { className: string; icon: typeof Clock }> = {
  pending: { className: "bg-amber-50 text-amber-700 ring-1 ring-amber-200", icon: Clock },
  confirmed: { className: "bg-blue-50 text-blue-700 ring-1 ring-blue-200", icon: CheckCircle2 },
  shipped: { className: "bg-violet-50 text-violet-700 ring-1 ring-violet-200", icon: Truck },
  delivered: { className: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200", icon: PackageCheck },
  cancelled: { className: "bg-red-50 text-red-700 ring-1 ring-red-200", icon: XCircle },
};

export function StatusBadge({ status }: { status: string }) {
  const meta = META[status] ?? { className: "bg-slate-100 text-slate-700 ring-1 ring-slate-200", icon: Clock };
  const Icon = meta.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full py-1 pl-2 pr-3 text-xs font-semibold capitalize ${meta.className}`}
    >
      <Icon size={13} />
      {status}
    </span>
  );
}
