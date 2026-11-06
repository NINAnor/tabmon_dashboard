"use client";

import { LogOut } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import useSWR from "swr";
import { SiteHeader } from "@/components/SiteHeader";
import { fetcher } from "@/lib/api";

export default function OpsLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { data, isLoading, mutate } = useSWR<{ user: string | null }>("/api/auth/me", fetcher);

  useEffect(() => {
    if (!isLoading && data && !data.user) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [data, isLoading, pathname, router]);

  if (!data?.user) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-white/40">Checking access…</div>
    );
  }

  return (
    <>
      <SiteHeader variant="ops" />
      <main className="mx-auto max-w-[1500px] px-6 pb-24 pt-24">
        <div className="mb-6 flex items-center justify-end gap-3 text-xs text-white/45">
          Signed in as {data.user}
          <button
            className="pill"
            onClick={async () => {
              await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
              await mutate();
            }}
          >
            <LogOut className="h-3.5 w-3.5" /> Sign out
          </button>
        </div>
        {children}
      </main>
    </>
  );
}
