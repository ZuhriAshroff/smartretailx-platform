import { useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";
import { listOrders, updateOrderStatus } from "../../api/orders";
import { extractErrorMessage } from "../../api/client";
import { useToast } from "../../components/Toast";
import { Pagination } from "../../components/Pagination";
import { StatusBadge } from "../../components/StatusBadge";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import type { OrderPublic, OrderStatus } from "../../types";

const PAGE_SIZE = 15;

const NEXT_STATUS: Record<string, OrderStatus[]> = {
  pending: ["cancelled"],
  confirmed: ["shipped", "cancelled"],
  shipped: ["delivered", "cancelled"],
  delivered: [],
  cancelled: [],
};

export function AdminOrdersPage() {
  const { showError, showSuccess } = useToast();
  const [orders, setOrders] = useState<OrderPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [cancelTarget, setCancelTarget] = useState<OrderPublic | null>(null);
  const [cancelling, setCancelling] = useState(false);

  function load() {
    setLoading(true);
    listOrders({ page, page_size: PAGE_SIZE, status: statusFilter || undefined })
      .then((data) => {
        setOrders(data.items);
        setTotal(data.total);
      })
      .catch((err) => showError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter]);

  async function transition(order: OrderPublic, status: OrderStatus) {
    try {
      await updateOrderStatus(order.id, status);
      showSuccess(`Order #${order.id} moved to ${status}`);
      load();
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  }

  async function confirmCancel() {
    if (!cancelTarget) return;
    setCancelling(true);
    try {
      await transition(cancelTarget, "cancelled");
      setCancelTarget(null);
    } finally {
      setCancelling(false);
    }
  }

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-900/8 text-neutral-700">
            <ClipboardList size={20} />
          </div>
          <h1 className="font-display text-xl font-bold text-neutral-900">All Orders</h1>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setPage(1);
            setStatusFilter(e.target.value);
          }}
          className="rounded-xl border border-white/60 bg-white/50 px-3 py-2 text-sm shadow-sm backdrop-blur-sm transition-colors focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
        >
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {loading ? (
        <p className="text-sm text-neutral-500">Loading...</p>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/50 bg-white/50 shadow-sm backdrop-blur-xl">
          <table className="w-full text-sm">
            <thead className="bg-white/30 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500 backdrop-blur-sm">
              <tr>
                <th className="px-4 py-2.5">Order</th>
                <th className="px-4 py-2.5">Customer</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Total</th>
                <th className="px-4 py-2.5">Placed</th>
                <th className="px-4 py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id} className="border-t border-white/50 transition-colors hover:bg-white/40">
                  <td className="px-4 py-2.5 font-medium text-neutral-900">#{order.id}</td>
                  <td className="px-4 py-2.5">#{order.customer_id}</td>
                  <td className="px-4 py-2.5">
                    <StatusBadge status={order.status} />
                  </td>
                  <td className="px-4 py-2.5">£{order.total_amount.toFixed(2)}</td>
                  <td className="px-4 py-2.5 text-neutral-500">{new Date(order.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex gap-2">
                      {(NEXT_STATUS[order.status] ?? []).map((next) => (
                        <button
                          key={next}
                          onClick={() => (next === "cancelled" ? setCancelTarget(order) : transition(order, next))}
                          className={`rounded-lg border px-2.5 py-1 text-xs font-semibold capitalize backdrop-blur-sm ${
                            next === "cancelled"
                              ? "border-red-200 bg-white/50 text-red-600 hover:bg-red-50"
                              : "border-neutral-200 bg-white/50 text-neutral-700 hover:bg-neutral-100"
                          }`}
                        >
                          {next}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />

      <ConfirmDialog
        open={cancelTarget !== null}
        onClose={() => setCancelTarget(null)}
        onConfirm={confirmCancel}
        title="Cancel order?"
        description={`Order #${cancelTarget?.id} will be marked cancelled. This cannot be undone.`}
        confirmLabel="Cancel Order"
        danger
        loading={cancelling}
      />
    </div>
  );
}
