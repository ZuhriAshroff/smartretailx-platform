import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Plus, Save, Trash2, Users, X } from "lucide-react";
import { changeUserRole, createUser, deleteUser, listUsers } from "../../api/users";
import { extractErrorMessage } from "../../api/client";
import { useToast } from "../../components/Toast";
import { Pagination } from "../../components/Pagination";
import { Modal } from "../../components/Modal";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { useAuth } from "../../auth/AuthContext";
import type { Role, UserPublic } from "../../types";

const PAGE_SIZE = 15;
const ROLES: Role[] = ["customer", "admin", "warehouse_staff"];
const inputClass =
  "w-full rounded-xl border border-white/60 bg-white/50 px-3 py-1.5 text-sm shadow-sm backdrop-blur-sm transition-colors focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10";

export function AdminUsersPage() {
  const { user: me } = useAuth();
  const { showError, showSuccess } = useToast();
  const [users, setUsers] = useState<UserPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", full_name: "", role: "customer" as Role });
  const [saving, setSaving] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<UserPublic | null>(null);
  const [deleting, setDeleting] = useState(false);

  function load() {
    setLoading(true);
    listUsers({ page, page_size: PAGE_SIZE })
      .then((data) => {
        setUsers(data.items);
        setTotal(data.total);
      })
      .catch((err) => showError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await createUser(form);
      showSuccess("User created");
      setShowForm(false);
      setForm({ email: "", password: "", full_name: "", role: "customer" });
      load();
    } catch (err) {
      showError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleRoleChange(user: UserPublic, role: Role) {
    try {
      await changeUserRole(user.id, role);
      showSuccess(`${user.email} is now ${role}`);
      load();
    } catch (err) {
      showError(extractErrorMessage(err));
    }
  }

  async function handleDelete(user: UserPublic) {
    setDeleting(true);
    try {
      await deleteUser(user.id);
      showSuccess("User deleted");
      setConfirmTarget(null);
      load();
    } catch (err) {
      showError(extractErrorMessage(err));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-900/8 text-neutral-700">
            <Users size={20} />
          </div>
          <h1 className="font-display text-xl font-bold text-neutral-900">Users</h1>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 rounded-xl bg-neutral-800 px-4 py-2 font-display text-sm font-semibold text-white shadow-md shadow-neutral-900/10 transition-colors hover:bg-neutral-700 active:bg-neutral-900"
        >
          <Plus size={16} />
          New User
        </button>
      </div>

      <Modal
        open={showForm}
        onClose={() => setShowForm(false)}
        title="New User"
        icon={
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-900/8 text-neutral-700">
            <Users size={16} />
          </div>
        }
        maxWidth="max-w-xl"
      >
        <form onSubmit={handleCreate} className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-700">Full name</label>
            <input
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-700">Email</label>
            <input
              required
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-700">Password</label>
            <input
              required
              type="password"
              minLength={8}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-700">Role</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
              className={inputClass}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div className="col-span-2 flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 rounded-xl bg-neutral-800 px-4 py-2 font-display text-sm font-semibold text-white shadow-md shadow-neutral-900/10 transition-colors hover:bg-neutral-700 active:bg-neutral-900 disabled:opacity-50"
            >
              <Save size={15} />
              {saving ? "Saving..." : "Create"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="flex items-center gap-2 rounded-xl border border-white/60 bg-white/40 px-4 py-2 text-sm font-medium text-neutral-600 backdrop-blur-sm hover:bg-white/70"
            >
              <X size={15} />
              Cancel
            </button>
          </div>
        </form>
      </Modal>

      {loading ? (
        <p className="text-sm text-neutral-500">Loading...</p>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/50 bg-white/50 shadow-sm backdrop-blur-xl">
          <table className="w-full text-sm">
            <thead className="bg-white/30 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500 backdrop-blur-sm">
              <tr>
                <th className="px-4 py-2.5">Name</th>
                <th className="px-4 py-2.5">Email</th>
                <th className="px-4 py-2.5">Role</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-t border-white/50 transition-colors hover:bg-white/40">
                  <td className="px-4 py-2.5 font-medium text-neutral-900">{user.full_name}</td>
                  <td className="px-4 py-2.5">{user.email}</td>
                  <td className="px-4 py-2.5">
                    <select
                      value={user.role}
                      disabled={user.id === me?.id}
                      onChange={(e) => handleRoleChange(user, e.target.value as Role)}
                      className="rounded-lg border border-white/60 bg-white/50 px-2 py-1 text-xs backdrop-blur-sm transition-colors focus:border-neutral-400 focus:outline-none disabled:bg-neutral-100/60"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                        user.is_active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                      }`}
                    >
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    {user.id !== me?.id && (
                      <button
                        onClick={() => setConfirmTarget(user)}
                        title="Delete"
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-neutral-600 hover:bg-red-50 hover:text-red-600"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />

      <ConfirmDialog
        open={confirmTarget !== null}
        onClose={() => setConfirmTarget(null)}
        onConfirm={() => confirmTarget && handleDelete(confirmTarget)}
        title="Delete user?"
        description={`${confirmTarget?.email} will be permanently deleted. This cannot be undone.`}
        confirmLabel="Delete"
        danger
        loading={deleting}
      />
    </div>
  );
}
