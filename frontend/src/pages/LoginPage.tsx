import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Boxes, LogIn, ShieldCheck } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { extractErrorMessage } from "../api/client";
import { useToast } from "../components/Toast";

export function LoginPage() {
  const { login } = useAuth();
  const { showError } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
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
          <h1 className="font-display text-xl font-bold text-neutral-900">Welcome back</h1>
          <p className="mt-1 text-sm text-neutral-500">Sign in to SmartRetailX</p>
        </div>

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
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-6 w-full rounded-xl border border-white/60 bg-white/50 px-3 py-2.5 text-sm text-neutral-900 shadow-sm transition-colors placeholder:text-neutral-400 focus:border-neutral-400 focus:bg-white/80 focus:outline-none focus:ring-2 focus:ring-neutral-900/10"
        />

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-neutral-800 py-2.5 font-display text-sm font-semibold text-white shadow-md shadow-neutral-900/10 transition-colors hover:bg-neutral-700 active:bg-neutral-900 disabled:opacity-50"
        >
          <LogIn size={16} />
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <p className="mt-4 text-center text-sm text-neutral-500">
          No account?{" "}
          <Link to="/register" className="font-medium text-neutral-900 underline decoration-neutral-300 underline-offset-2 hover:decoration-neutral-900">
            Register
          </Link>
        </p>

        <div className="mt-6 rounded-xl border border-white/50 bg-white/40 p-3 text-xs text-neutral-600 backdrop-blur-sm">
          <p className="mb-1 flex items-center gap-1 font-display font-semibold text-neutral-800">
            <ShieldCheck size={13} />
            Demo accounts
          </p>
          <p>admin@smartretailx.com / Admin123!</p>
          <p>staff@smartretailx.com / Staff123!</p>
          <p>customer@smartretailx.com / Customer123!</p>
        </div>
      </form>
    </div>
  );
}
