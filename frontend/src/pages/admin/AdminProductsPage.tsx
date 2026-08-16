import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { PackagePlus, PackageX, Pencil, Plus, Save, X } from "lucide-react";
import { createProduct, deleteProduct, listProducts, updateProduct } from "../../api/products";
import { extractErrorMessage } from "../../api/client";
import { useToast } from "../../components/Toast";
import { Pagination } from "../../components/Pagination";
import { Modal } from "../../components/Modal";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import type { ProductCreateInput, ProductPublic } from "../../types";

const PAGE_SIZE = 15;
const EMPTY_FORM: ProductCreateInput = { sku: "", name: "", description: "", category: "", price: 0, currency: "GBP" };
const inputClass =
  "w-full rounded-xl border border-white/60 bg-white/50 px-3 py-1.5 text-sm shadow-sm backdrop-blur-sm transition-colors focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10 disabled:bg-neutral-100/60";

export function AdminProductsPage() {
  const { showError, showSuccess } = useToast();
  const [products, setProducts] = useState<ProductPublic[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<ProductCreateInput>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<ProductPublic | null>(null);
  const [deleting, setDeleting] = useState(false);

  function load() {
    setLoading(true);
    listProducts({ page, page_size: PAGE_SIZE })
      .then((data) => {
        setProducts(data.items);
        setTotal(data.total);
      })
      .catch((err) => showError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  }

  function openEdit(product: ProductPublic) {
    setEditingId(product.id);
    setForm({
      sku: product.sku,
      name: product.name,
      description: product.description,
      category: product.category,
      price: product.price,
      currency: product.currency,
    });
    setShowForm(true);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingId === null) {
        await createProduct(form);
        showSuccess("Product created");
      } else {
        await updateProduct(editingId, {
          name: form.name,
          description: form.description,
          category: form.category,
          price: form.price,
          currency: form.currency,
        });
        showSuccess("Product updated");
      }
      setShowForm(false);
      load();
    } catch (err) {
      showError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(product: ProductPublic) {
    setDeleting(true);
    try {
      await deleteProduct(product.id);
      showSuccess("Product deactivated");
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
            <PackagePlus size={20} />
          </div>
          <h1 className="font-display text-xl font-bold text-neutral-900">Manage Products</h1>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 rounded-xl bg-neutral-800 px-4 py-2 font-display text-sm font-semibold text-white shadow-md shadow-neutral-900/10 transition-colors hover:bg-neutral-700 active:bg-neutral-900"
        >
          <Plus size={16} />
          New Product
        </button>
      </div>

      <Modal
        open={showForm}
        onClose={() => setShowForm(false)}
        title={editingId === null ? "New Product" : "Edit Product"}
        icon={
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-900/8 text-neutral-700">
            <PackagePlus size={16} />
          </div>
        }
        maxWidth="max-w-xl"
      >
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-700">SKU</label>
            <input
              required
              disabled={editingId !== null}
              value={form.sku}
              onChange={(e) => setForm({ ...form, sku: e.target.value })}
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-700">Name</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} />
          </div>
          <div className="col-span-2">
            <label className="mb-1 block text-xs font-medium text-neutral-700">Description</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className={inputClass}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-neutral-700">Category</label>
            <input
              required
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className={inputClass}
            />
          </div>
          <div className="flex gap-2">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-neutral-700">Price</label>
              <input
                required
                type="number"
                min={0.01}
                step={0.01}
                value={form.price}
                onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
                className={inputClass}
              />
            </div>
            <div className="w-24">
              <label className="mb-1 block text-xs font-medium text-neutral-700">Currency</label>
              <input
                required
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
                className={inputClass}
              />
            </div>
          </div>
          <div className="col-span-2 flex gap-2">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 rounded-xl bg-neutral-800 px-4 py-2 font-display text-sm font-semibold text-white shadow-md shadow-neutral-900/10 transition-colors hover:bg-neutral-700 active:bg-neutral-900 disabled:opacity-50"
            >
              <Save size={15} />
              {saving ? "Saving..." : "Save"}
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
                <th className="px-4 py-2.5">SKU</th>
                <th className="px-4 py-2.5">Name</th>
                <th className="px-4 py-2.5">Category</th>
                <th className="px-4 py-2.5">Price</th>
                <th className="px-4 py-2.5">Status</th>
                <th className="px-4 py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-t border-white/50 transition-colors hover:bg-white/40">
                  <td className="px-4 py-2.5 text-neutral-500">{product.sku}</td>
                  <td className="px-4 py-2.5 font-medium text-neutral-900">{product.name}</td>
                  <td className="px-4 py-2.5">{product.category}</td>
                  <td className="px-4 py-2.5">
                    {product.currency} {product.price.toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                        product.is_active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
                      }`}
                    >
                      {product.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex gap-1">
                      <button
                        onClick={() => openEdit(product)}
                        title="Edit"
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-neutral-600 hover:bg-neutral-100"
                      >
                        <Pencil size={15} />
                      </button>
                      {product.is_active && (
                        <button
                          onClick={() => setConfirmTarget(product)}
                          title="Deactivate"
                          className="flex h-8 w-8 items-center justify-center rounded-lg text-neutral-600 hover:bg-red-50 hover:text-red-600"
                        >
                          <PackageX size={15} />
                        </button>
                      )}
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
        open={confirmTarget !== null}
        onClose={() => setConfirmTarget(null)}
        onConfirm={() => confirmTarget && handleDelete(confirmTarget)}
        title="Deactivate product?"
        description={`"${confirmTarget?.name}" will be marked inactive and hidden from the catalogue. This can be reversed by editing it later.`}
        confirmLabel="Deactivate"
        danger
        loading={deleting}
      />
    </div>
  );
}
