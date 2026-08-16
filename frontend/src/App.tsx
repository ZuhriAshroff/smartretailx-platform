import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ToastProvider } from "./components/Toast";
import { PrivateRoute, RoleRoute } from "./auth/PrivateRoute";
import { Layout } from "./components/Layout";
import { AmbientBackground } from "./components/AmbientBackground";
import { HomeRedirect } from "./components/HomeRedirect";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ProductsPage } from "./pages/ProductsPage";
import { OrdersPage } from "./pages/OrdersPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { AdminOrdersPage } from "./pages/admin/AdminOrdersPage";
import { AdminProductsPage } from "./pages/admin/AdminProductsPage";
import { AdminInventoryPage } from "./pages/admin/AdminInventoryPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";

export default function App() {
  return (
    <BrowserRouter>
      <AmbientBackground />
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            <Route element={<PrivateRoute />}>
              <Route element={<Layout />}>
                <Route path="/" element={<HomeRedirect />} />
                <Route path="/products" element={<ProductsPage />} />
                <Route path="/orders" element={<OrdersPage />} />
                <Route path="/notifications" element={<NotificationsPage />} />

                <Route element={<RoleRoute allow={["admin", "warehouse_staff"]} />}>
                  <Route path="/admin/orders" element={<AdminOrdersPage />} />
                  <Route path="/admin/inventory" element={<AdminInventoryPage />} />
                </Route>

                <Route element={<RoleRoute allow={["admin"]} />}>
                  <Route path="/admin/products" element={<AdminProductsPage />} />
                  <Route path="/admin/users" element={<AdminUsersPage />} />
                </Route>
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
