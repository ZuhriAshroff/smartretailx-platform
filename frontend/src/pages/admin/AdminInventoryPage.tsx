import { useEffect, useState } from "react";
import { AlertTriangle, Boxes, RefreshCw } from "lucide-react";
import { adjustInventory, listInventory } from "../../api/inventory";
import { extractErrorMessage } from "../../api/client";
import { useToast } from "../../components/Toast";
import { Pagination } from "../../components/Pagination";
import type { InventoryPublic } from "../../types";

const PAGE_SIZE = 15;

export function AdminInventoryPage() {
  const { showError, showSuccess } = useToast();
  const [items, setItems] = useState<InventoryPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [deltas, setDeltas] = useState<Record<number, string>>({});

  function load() {
    setLoading(true);
    listInventory({ page, page_size: PAGE_SIZE })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((err) => showError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  async function applyDelta(productId: number) {
    const raw = deltas[productId];
    const delta = Number(raw);
    if (!raw || Number.isNaN(delta) || delta === 0) {
      showError("Enter a non-zero quantity change");
      return;
    }
    try {
      await adjustInventory(productId, { quantity_delta: delta });
      showSuccess("Stock updated");
      setDeltas((prev) => ({ ...prev, [productId]: "" }));
      load();
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  }

  const lowStockCount = items.filter((i) => i.quantity_available <= i.reorder_level).length;

  return (
    <div>
      <div className="mb-2 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-900/8 text-neutral-700">
          <Boxes size={20} />
        </div>
        <h1 className="font-display text-xl font-bold text-neutral-900">Inventory</h1>
      </div>

      {lowStockCount > 0 && (
        <div className="mb-4 mt-3 flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <AlertTriangle size={18} className="shrink-0" />
          <span>
            <strong>{lowStockCount}</strong> product{lowStockCount === 1 ? "" : "s"} on this page{" "}
            {lowStockCount === 1 ? "is" : "are"} at or below its reorder level.
          </span>
        </div>
      )}

      {loading ? (
        <p className="mt-4 text-sm text-neutral-500">Loading...</p>
      ) : (
        <div className="mt-4 overflow-hidden rounded-2xl border border-white/50 bg-white/50 shadow-sm backdrop-blur-xl">
          <table className="w-full text-sm">
            <thead className="bg-white/30 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500 backdrop-blur-sm">
              <tr>
                <th className="px-4 py-2.5">SKU</th>
                <th className="px-4 py-2.5">Product ID</th>
                <th className="px-4 py-2.5">Available</th>
                <th className="px-4 py-2.5">Reserved</th>
                <th className="px-4 py-2.5">Reorder Level</th>
                <th className="px-4 py-2.5">Adjust Stock</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const lowStock = item.quantity_available <= item.reorder_level;
                return (
                  <tr
                    key={item.id}
                    className={`border-t border-white/50 transition-colors ${lowStock ? "bg-amber-50/50" : "hover:bg-white/40"}`}
                  >
                    <td className="px-4 py-2.5 text-neutral-500">{item.sku || "—"}</td>
                    <td className="px-4 py-2.5">#{item.product_id}</td>
                    <td className="px-4 py-2.5 font-medium text-neutral-900">
                      <span className="inline-flex items-center gap-1.5">
                        {item.quantity_available}
                        {lowStock && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700">
                            <AlertTriangle size={11} />
                            LOW
                          </span>
                        )}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">{item.quantity_reserved}</td>
                    <td className="px-4 py-2.5">{item.reorder_level}</td>
                    <td className="px-4 py-2.5">
                      <div className="flex gap-2">
                        <input
                          type="number"
                          placeholder="+10 / -5"
                          value={deltas[item.product_id] ?? ""}
                          onChange={(e) => setDeltas((prev) => ({ ...prev, [item.product_id]: e.target.value }))}
                          className="w-24 rounded-xl border border-white/60 bg-white/50 px-2 py-1.5 text-sm shadow-sm backdrop-blur-sm transition-colors focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
                        />
                        <button
                          onClick={() => applyDelta(item.product_id)}
                          className="flex items-center gap-1.5 rounded-xl border border-neutral-200 bg-white/50 px-3 py-1.5 text-xs font-semibold text-neutral-700 backdrop-blur-sm hover:bg-neutral-100"
                        >
                          <RefreshCw size={13} />
                          Apply
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />
    </div>
  );
}
