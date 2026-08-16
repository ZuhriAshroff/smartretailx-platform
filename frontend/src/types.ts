export type Role = "customer" | "admin" | "warehouse_staff";

export interface UserPublic {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
}

export interface JwtPayload {
  sub: string;
  email: string;
  role: Role;
  exp: number;
  iat: number;
}

export interface ProductPublic {
  id: number;
  sku: string;
  name: string;
  description: string;
  category: string;
  price: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreateInput {
  sku: string;
  name: string;
  description: string;
  category: string;
  price: number;
  currency: string;
}

export interface ProductUpdateInput {
  name?: string;
  description?: string;
  category?: string;
  price?: number;
  currency?: string;
  is_active?: boolean;
}

export type OrderStatus = "pending" | "confirmed" | "shipped" | "delivered" | "cancelled";

export interface OrderItemPublic {
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
}

export interface OrderPublic {
  id: number;
  customer_id: number;
  status: OrderStatus;
  total_amount: number;
  items: OrderItemPublic[];
  created_at: string;
  updated_at: string;
}

export interface InventoryPublic {
  id: number;
  product_id: number;
  sku: string;
  quantity_available: number;
  quantity_reserved: number;
  reorder_level: number;
  updated_at: string;
}

export interface NotificationPublic {
  id: number;
  recipient_user_id: number | null;
  recipient_email: string | null;
  event_type: string;
  subject: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface Paginated<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}
