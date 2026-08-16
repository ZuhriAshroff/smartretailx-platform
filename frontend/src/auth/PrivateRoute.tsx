import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { Role } from "../types";

export function PrivateRoute() {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

export function RoleRoute({ allow }: { allow: Role[] }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!allow.includes(user.role)) return <Navigate to="/" replace />;
  return <Outlet />;
}
