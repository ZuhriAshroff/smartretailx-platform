import { Fragment, useEffect, useState } from "react";
import { ClipboardList, Inbox } from "lucide-react";
import { listOrders } from "../api/orders";
import { extractErrorMessage } from "../api/client";
import { useToast } from "../components/Toast";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import type { OrderPublic } from "../types";

const PAGE_SIZE = 10;

export function OrdersPage() {
  const { showError } = useToast();
  const [orders, setOrders] = useState<OrderPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listOrders({ page, page_size: PAGE_SIZE })
      .then((data) => {
        if (cancelled) return;
        setOrders(data.items);
        setTotal(data.total);
      })
      .catch((err) => !cancelled && showError(extractErrorMessage(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  return (
    <div>
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-900/8 text-neutral-700">
          <ClipboardList size={20} />
        </div>
        <h1 className="font-display text-xl font-bold text-neutral-900">My Orders</h1>
      </div>

      {loading ? (
        <p className="text-sm text-neutral-500">Loading...</p>
      ) : orders.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-neutral-900/8 text-neutral-400">
            <Inbox size={22} />
          </div>
          <p className="text-sm text-neutral-500">You haven't placed any orders yet.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/50 bg-white/50 shadow-sm backdrop-blur-xl">
          <table className="w-full text-sm">
            <thead className="bg-white/30 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500 backdrop-blur-sm">
              <tr>
                <th className="px-4 py-2.5">Order</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Total</th>
                <th className="px-4 py-2.5">Placed</th>
                <th className="px-4 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <Fragment key={order.id}>
                  <tr className="border-t border-white/50 transition-colors hover:bg-white/40">
                    <td className="px-4 py-2.5 font-medium text-neutral-900">#{order.id}</td>
                    <td className="px-4 py-2.5">
                      <StatusBadge status={order.status} />
                    </td>
                    <td className="px-4 py-2.5">£{order.total_amount.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-neutral-500">{new Date(order.created_at).toLocaleString()}</td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={() => setExpanded(expanded === order.id ? null : order.id)}
                        className="text-xs font-semibold text-neutral-900 underline decoration-neutral-300 underline-offset-2 hover:decoration-neutral-900"
                      >
                        {expanded === order.id ? "Hide" : "Details"}
                      </button>
                    </td>
                  </tr>
                  {expanded === order.id && (
                    <tr className="border-t border-white/50 bg-white/30">
                      <td colSpan={5} className="px-4 py-3">
                        <ul className="space-y-1 text-xs text-neutral-600">
                          {order.items.map((item) => (
                            <li key={item.product_id} className="flex justify-between">
                              <span>
                                {item.product_name} x{item.quantity}
                              </span>
                              <span>£{(item.unit_price * item.quantity).toFixed(2)}</span>
                            </li>
                          ))}
                        </ul>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />
    </div>
  );
}
