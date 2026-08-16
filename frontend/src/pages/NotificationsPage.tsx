import { useEffect, useState } from "react";
import { Bell, BellOff } from "lucide-react";
import { listNotifications, markNotificationRead } from "../api/notifications";
import { extractErrorMessage } from "../api/client";
import { useToast } from "../components/Toast";
import { Pagination } from "../components/Pagination";
import type { NotificationPublic } from "../types";

const PAGE_SIZE = 15;

export function NotificationsPage() {
  const { showError } = useToast();
  const [notifications, setNotifications] = useState<NotificationPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    listNotifications({ page, page_size: PAGE_SIZE })
      .then((data) => {
        setNotifications(data.items);
        setTotal(data.total);
      })
      .catch((err) => showError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  async function markRead(id: number) {
    try {
      await markNotificationRead(id);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-900/8 text-neutral-700">
          <Bell size={20} />
        </div>
        <h1 className="font-display text-xl font-bold text-neutral-900">Notifications</h1>
      </div>

      {loading ? (
        <p className="text-sm text-neutral-500">Loading...</p>
      ) : notifications.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-neutral-900/8 text-neutral-400">
            <BellOff size={22} />
          </div>
          <p className="text-sm text-neutral-500">No notifications.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`rounded-2xl border p-3.5 shadow-sm backdrop-blur-xl ${
                n.is_read ? "border-white/40 bg-white/30" : "border-neutral-300/70 bg-white/60"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="flex items-center gap-2 text-sm font-semibold text-neutral-900">
                    {!n.is_read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-neutral-800" />}
                    {n.subject}
                  </p>
                  <p className="text-sm text-neutral-600">{n.message}</p>
                  <p className="mt-1 text-xs text-neutral-400">
                    {n.event_type} &middot; {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
                {!n.is_read && (
                  <button
                    onClick={() => markRead(n.id)}
                    className="whitespace-nowrap text-xs font-semibold text-neutral-900 underline decoration-neutral-300 underline-offset-2 hover:decoration-neutral-900"
                  >
                    Mark read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />
    </div>
  );
}
