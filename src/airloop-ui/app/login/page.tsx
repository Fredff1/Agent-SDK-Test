"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("airloop_user");
    if (raw) {
      router.replace("/");
    }
  }, [router]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const user = await login(username.trim(), password);
      localStorage.setItem("airloop_user", JSON.stringify(user));
      router.replace("/");
    } catch (err: any) {
      setError("Invalid username or password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <div className="mx-auto flex min-h-screen max-w-4xl items-center justify-center px-4 py-12">
        <div className="w-full max-w-md rounded-3xl border border-border-subtle bg-white/90 p-8 shadow-panel backdrop-blur">
          <div className="mb-6">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              Airloop Access
            </div>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">
              Sign in to continue
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              Use your assigned demo account to view chat sessions.
            </p>
          </div>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Username
              </label>
              <input
                type="text"
                className="mt-2 w-full rounded-xl border border-border-subtle bg-white px-3 py-2 text-sm text-slate-800 shadow-soft focus:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/10"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="Amy / bob / Alex"
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Password
              </label>
              <input
                type="password"
                className="mt-2 w-full rounded-xl border border-border-subtle bg-white px-3 py-2 text-sm text-slate-800 shadow-soft focus:border-brand/40 focus:outline-none focus:ring-2 focus:ring-brand/10"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••"
                autoComplete="current-password"
                required
              />
            </div>
            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-2 w-full rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-soft transition-opacity duration-200 hover:opacity-90 disabled:opacity-60"
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
          <div className="mt-6 text-xs text-slate-500">
            Demo accounts use password: <span className="font-semibold">123456</span>
          </div>
        </div>
      </div>
    </main>
  );
}
