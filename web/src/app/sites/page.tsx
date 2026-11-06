"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import useSWR from "swr";
import { PlacesView } from "@/components/PlaceExplorer";
import { PublicShell } from "@/components/SiteHeader";
import { fetcher, type Cluster } from "@/lib/api";

function Sites() {
  const router = useRouter();
  const id = useSearchParams().get("id");
  const { data: clusters = [] } = useSWR<Cluster[]>("/api/public/clusters", fetcher);
  if (!clusters.length) return <div className="mx-auto mt-10 h-[600px] max-w-7xl animate-pulse rounded-2xl bg-white/5" />;
  return (
    <PlacesView
      clusters={clusters}
      id={id}
      onChange={(next) => router.replace(`/sites?id=${encodeURIComponent(next)}`, { scroll: false })}
    />
  );
}

export default function SitesPage() {
  return (
    <PublicShell>
      <Suspense>
        <Sites />
      </Suspense>
    </PublicShell>
  );
}
