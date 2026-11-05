"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";

function LoginForm() {
  const router = useRouter();
  const next = useSearchParams().get("next") || "/ops";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });
    setBusy(false);
    if (res.ok) router.replace(next.startsWith("/") ? next : "/ops");
    else setError(res.status === 401 ? "Wrong username or password" : "Login is not available right now");
  };

  return (
    <form onSubmit={submit} className="card w-full max-w-sm space-y-4 p-8">
      <div>
        <p className="eyebrow">TABMON team</p>
        <h1 className="mt-2 font-serif text-3xl">Sign in</h1>
        <p className="mt-2 text-sm text-white/50">
          The team area shows exact device locations, health and deployment photos.
        </p>
      </div>
      <input className="input" placeholder="Username" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} />
      <input
        className="input"
        placeholder="Password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <p className="text-sm text-coral">{error}</p>}
      <button disabled={busy} className="w-full rounded-full bg-teal py-2.5 text-sm font-medium text-ocean-950 disabled:opacity-60">
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}

export default function LoginPage() {
  return (
    <>
      <SiteHeader />
      <main className="flex min-h-screen items-center justify-center px-6">
        <Suspense>
          <LoginForm />
        </Suspense>
      </main>
    </>
  );
}
