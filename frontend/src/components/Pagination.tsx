import { ChevronLeft, ChevronRight } from "lucide-react";

export function Pagination({
  page,
  pageSize,
  total,
  onChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;

  return (
    <div className="mt-4 flex items-center justify-between text-sm text-neutral-600">
      <span>
        Page <span className="rounded-md bg-neutral-800 px-2 py-0.5 font-display font-semibold text-white">{page}</span> of{" "}
        {totalPages} &middot; {total} total
      </span>
      <div className="flex gap-2">
        <button
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          className="flex items-center gap-1 rounded-xl border border-white/60 bg-white/40 px-3 py-1.5 text-sm font-medium text-neutral-600 backdrop-blur-sm hover:bg-white/70 hover:text-neutral-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white/40 disabled:hover:text-neutral-600"
        >
          <ChevronLeft size={16} />
          Previous
        </button>
        <button
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          className="flex items-center gap-1 rounded-xl border border-white/60 bg-white/40 px-3 py-1.5 text-sm font-medium text-neutral-600 backdrop-blur-sm hover:bg-white/70 hover:text-neutral-900 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-white/40 disabled:hover:text-neutral-600"
        >
          Next
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
