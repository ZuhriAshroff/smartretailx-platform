import { NavLink, Outlet } from "react-router-dom";
import {
  Bell,
  Boxes,
  ClipboardList,
  LogOut,
  PackagePlus,
  ShieldCheck,
  ShoppingBag,
  User as UserIcon,
  Users,
  Warehouse,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-xl px-3 py-2.5 font-display text-sm font-medium transition-all ${
    isActive
      ? "bg-neutral-800 text-white shadow-sm shadow-neutral-900/10"
      : "text-neutral-600 hover:bg-white/50 hover:text-neutral-900"
  }`;

const ROLE_META: Record<string, { label: string; icon: typeof ShieldCheck; className: string }> = {
  admin: { label: "Admin", icon: ShieldCheck, className: "bg-neutral-900/8 text-neutral-700" },
  warehouse_staff: { label: "Warehouse", icon: Warehouse, className: "bg-amber-100/80 text-amber-700" },
  customer: { label: "Customer", icon: UserIcon, className: "bg-neutral-900/8 text-neutral-700" },
};

export function Layout() {
  const { user, logout } = useAuth();
  const roleMeta = user ? ROLE_META[user.role] : undefined;
  const RoleIcon = roleMeta?.icon ?? UserIcon;
  const initials = user?.email?.slice(0, 2).toUpperCase() ?? "?";

  return (
    <div className="flex min-h-screen items-stretch p-3 lg:p-5">
      <div className="flex w-full overflow-hidden rounded-[2rem] border border-white/50 bg-white/25 shadow-2xl shadow-neutral-300/40 backdrop-blur-2xl">
        <aside className="flex w-64 shrink-0 flex-col border-r border-white/40 bg-white/15 px-4 py-6">
          <div className="mb-8 flex items-center gap-2.5 px-1">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-800 shadow-sm shadow-neutral-900/10">
              <Boxes size={20} className="text-white" />
            </div>
            <span className="font-display text-base font-bold text-neutral-900">SmartRetailX</span>
          </div>

          <nav className="flex flex-1 flex-col gap-1">
            {user?.role === "customer" && (
              <>
                <NavLink to="/products" className={linkClass}>
                  <ShoppingBag size={18} />
                  Products
                </NavLink>
                <NavLink to="/orders" className={linkClass}>
                  <ClipboardList size={18} />
                  My Orders
                </NavLink>
              </>
            )}
            <NavLink to="/notifications" className={linkClass}>
              <Bell size={18} />
              Notifications
            </NavLink>

            {(user?.role === "admin" || user?.role === "warehouse_staff") && (
              <>
                <div className="mb-1 mt-5 px-3 font-display text-xs font-semibold uppercase tracking-wide text-neutral-400">
                  Admin
                </div>
                <NavLink to="/admin/orders" className={linkClass}>
                  <ClipboardList size={18} />
                  All Orders
                </NavLink>
                <NavLink to="/admin/inventory" className={linkClass}>
                  <Boxes size={18} />
                  Inventory
                </NavLink>
                {user?.role === "admin" && (
                  <>
                    <NavLink to="/admin/products" className={linkClass}>
                      <PackagePlus size={18} />
                      Manage Products
                    </NavLink>
                    <NavLink to="/admin/users" className={linkClass}>
                      <Users size={18} />
                      Users
                    </NavLink>
                  </>
                )}
              </>
            )}
          </nav>

          <div className="mt-4 flex items-center gap-2.5 rounded-xl bg-white/40 p-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-neutral-800 font-display text-xs font-semibold text-white">
              {initials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-neutral-800">{user?.email}</p>
              {roleMeta && (
                <span
                  className={`mt-0.5 inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${roleMeta.className}`}
                >
                  <RoleIcon size={11} />
                  {roleMeta.label}
                </span>
              )}
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-neutral-500 hover:bg-white/70 hover:text-neutral-900"
            >
              <LogOut size={16} />
            </button>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1600px] px-6 py-8 lg:px-10">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
