import { useEffect, useState } from "react";
import { Minus, PackageOpen, Plus, Search, ShoppingBag, ShoppingCart } from "lucide-react";
import { listProducts } from "../api/products";
import { createOrder } from "../api/orders";
import { extractErrorMessage } from "../api/client";
import { useToast } from "../components/Toast";
import { Pagination } from "../components/Pagination";
import { useAuth } from "../auth/AuthContext";
import type { ProductPublic } from "../types";

const PAGE_SIZE = 12;

export function ProductsPage() {
  const { user } = useAuth();
  const { showError, showSuccess } = useToast();
  const [products, setProducts] = useState<ProductPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState<Record<number, number>>({});
  const [placingOrder, setPlacingOrder] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listProducts({ q: query || undefined, category: category || undefined, page, page_size: PAGE_SIZE })
      .then((data) => {
        if (cancelled) return;
        setProducts(data.items);
        setTotal(data.total);
      })
      .catch((err) => !cancelled && showError(extractErrorMessage(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, category, page]);

  function setQty(productId: number, qty: number) {
    setCart((prev) => {
      const next = { ...prev };
      if (qty <= 0) delete next[productId];
      else next[productId] = qty;
      return next;
    });
  }

  const cartItems = Object.entries(cart).map(([productId, quantity]) => ({
    product: products.find((p) => p.id === Number(productId)),
    quantity,
  }));
  const cartTotal = cartItems.reduce((sum, item) => sum + (item.product?.price ?? 0) * item.quantity, 0);

  async function placeOrder() {
    if (Object.keys(cart).length === 0) return;
    setPlacingOrder(true);
    try {
      await createOrder({
        items: Object.entries(cart).map(([productId, quantity]) => ({
          product_id: Number(productId),
          quantity,
        })),
      });
      showSuccess("Order placed successfully");
      setCart({});
    } catch (err) {
      showError(extractErrorMessage(err));
    } finally {
      setPlacingOrder(false);
    }
  }

  return (
    <div className={`grid grid-cols-1 gap-6 ${user?.role === "customer" ? "xl:grid-cols-[1fr_340px]" : ""}`}>
      <div>
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-900/8 text-neutral-700">
            <ShoppingBag size={20} />
          </div>
          <div>
            <h1 className="font-display text-xl font-bold text-neutral-900">Browse Products</h1>
            <p className="text-sm text-neutral-500">Search the catalogue and build an order</p>
          </div>
        </div>

        <div className="mb-5 flex gap-2">
          <div className="relative flex-1">
            <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              placeholder="Search products..."
              value={query}
              onChange={(e) => {
                setPage(1);
                setQuery(e.target.value);
              }}
              className="w-full rounded-xl border border-white/60 bg-white/50 py-2 pl-9 pr-3 text-sm shadow-sm backdrop-blur-sm transition-colors placeholder:text-neutral-400 focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
            />
          </div>
          <input
            placeholder="Category"
            value={category}
            onChange={(e) => {
              setPage(1);
              setCategory(e.target.value);
            }}
            className="w-40 rounded-xl border border-white/60 bg-white/50 px-3 py-2 text-sm shadow-sm backdrop-blur-sm transition-colors placeholder:text-neutral-400 focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
          />
        </div>

        {loading ? (
          <p className="text-sm text-neutral-500">Loading...</p>
        ) : products.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-neutral-900/8 text-neutral-400">
              <PackageOpen size={22} />
            </div>
            <p className="text-sm text-neutral-500">No products found.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
            {products.map((product) => (
              <div
                key={product.id}
                className="flex flex-col rounded-2xl border border-white/50 bg-white/45 p-5 shadow-sm backdrop-blur-xl transition-shadow hover:shadow-md"
              >
                <div className="mb-1.5 flex items-start justify-between gap-2">
                  <h3 className="font-semibold leading-snug text-neutral-900">{product.name}</h3>
                  <span className="shrink-0 text-xs text-neutral-400">{product.sku}</span>
                </div>
                <p className="mb-3 line-clamp-2 text-sm text-neutral-500">{product.description}</p>
                <span className="mb-4 inline-flex w-fit items-center rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-indigo-600 ring-1 ring-indigo-100">
                  {product.category}
                </span>
                <div className="mt-auto flex items-end justify-between pt-2">
                  <span className="font-display text-2xl font-bold text-indigo-600">
                    {product.currency} {product.price.toFixed(2)}
                  </span>
                  {user?.role === "customer" && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setQty(product.id, (cart[product.id] ?? 0) - 1)}
                        className="flex h-8 w-8 items-center justify-center rounded-full border border-neutral-200 text-neutral-700 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-600"
                      >
                        <Minus size={14} />
                      </button>
                      <span className="w-5 text-center text-sm font-semibold">{cart[product.id] ?? 0}</span>
                      <button
                        onClick={() => setQty(product.id, (cart[product.id] ?? 0) + 1)}
                        className="flex h-8 w-8 items-center justify-center rounded-full border border-neutral-200 text-neutral-700 hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-600"
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <Pagination page={page} pageSize={PAGE_SIZE} total={total} onChange={setPage} />
      </div>

      {user?.role === "customer" && (
        <div className="h-fit rounded-2xl border border-white/50 bg-white/45 p-5 shadow-sm backdrop-blur-xl">
          <div className="mb-3 flex items-center gap-2">
            <ShoppingCart size={17} className="text-neutral-700" />
            <h2 className="font-display font-semibold text-neutral-900">Your Order</h2>
          </div>
          {cartItems.length === 0 ? (
            <p className="text-sm text-neutral-500">Add products to build an order.</p>
          ) : (
            <>
              <ul className="mb-3 space-y-2 text-sm">
                {cartItems.map(
                  (item) =>
                    item.product && (
                      <li key={item.product.id} className="flex justify-between">
                        <span>
                          {item.product.name} x{item.quantity}
                        </span>
                        <span>{(item.product.price * item.quantity).toFixed(2)}</span>
                      </li>
                    ),
                )}
              </ul>
              <div className="mb-3 flex items-baseline justify-between border-t border-white/60 pt-2">
                <span className="font-semibold text-neutral-900">Total</span>
                <span className="font-display text-lg font-bold text-indigo-600">{cartTotal.toFixed(2)}</span>
              </div>
              <button
                onClick={placeOrder}
                disabled={placingOrder}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-neutral-800 py-2.5 font-display text-sm font-semibold text-white shadow-md shadow-neutral-900/10 transition-colors hover:bg-neutral-700 active:bg-neutral-900 disabled:opacity-50"
              >
                {placingOrder ? "Placing order..." : "Place Order"}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
