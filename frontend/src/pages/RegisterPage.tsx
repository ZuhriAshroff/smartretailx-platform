import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Boxes, UserPlus } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { extractErrorMessage } from "../api/client";
import { useToast } from "../components/Toast";

export function RegisterPage() {
  const { register } = useAuth();
  const { showError } = useToast();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await register(email, password, fullName);
      navigate("/products", { replace: true });
    } catch (err) {
      showError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6 py-12">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-3xl border border-white/50 bg-white/35 p-8 shadow-2xl shadow-neutral-300/50 backdrop-blur-2xl"
      >
        <div className="mb-7 flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-neutral-800 shadow-sm shadow-neutral-900/10">
            <Boxes size={24} className="text-white" />
          </div>
          <h1 className="font-display text-xl font-bold text-neutral-900">Create your account</h1>
          <p className="mt-1 text-sm text-neutral-500">Register as a customer</p>
        </div>

        <label className="mb-1 block text-sm font-medium text-neutral-700">Full name</label>
        <input
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="mb-4 w-full rounded-xl border border-white/60 bg-white/50 px-3 py-2.5 text-sm text-neutral-900 shadow-sm transition-colors placeholder:text-neutral-400 focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
        />

        <label className="mb-1 block text-sm font-medium text-neutral-700">Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-4 w-full rounded-xl border border-white/60 bg-white/50 px-3 py-2.5 text-sm text-neutral-900 shadow-sm transition-colors placeholder:text-neutral-400 focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
        />

        <label className="mb-1 block text-sm font-medium text-neutral-700">Password</label>
        <input
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-6 w-full rounded-xl border border-white/60 bg-white/50 px-3 py-2.5 text-sm text-neutral-900 shadow-sm transition-colors placeholder:text-neutral-400 focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
        />

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-neutral-800 py-2.5 font-display text-sm font-semibold text-white shadow-md shadow-neutral-900/10 transition-colors hover:bg-neutral-700 active:bg-neutral-900 disabled:opacity-50"
        >
          <UserPlus size={16} />
          {loading ? "Creating account..." : "Register"}
        </button>

        <p className="mt-4 text-center text-sm text-neutral-500">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-neutral-900 underline decoration-neutral-300 underline-offset-2 hover:decoration-neutral-900">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
