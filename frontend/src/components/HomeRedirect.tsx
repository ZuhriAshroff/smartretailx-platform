import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const ROLE_HOME: Record<string, string> = {
  customer: "/products",
  admin: "/admin/orders",
  warehouse_staff: "/admin/inventory",
};

export function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={(user && ROLE_HOME[user.role]) || "/products"} replace />;
}
