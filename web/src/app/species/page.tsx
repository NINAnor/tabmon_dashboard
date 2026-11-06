"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback } from "react";
import useSWR from "swr";
import { PublicShell } from "@/components/SiteHeader";
import { SpeciesView } from "@/components/SpeciesView";
import { fetcher, type Cluster } from "@/lib/api";

function Species() {
  const router = useRouter();
  const species = useSearchParams().get("species");
  const { data: clusters = [] } = useSWR<Cluster[]>("/api/public/clusters", fetcher);
  const onSpecies = useCallback(
    (s: string) => router.replace(`/species?species=${encodeURIComponent(s)}`, { scroll: false }),
    [router],
  );
  return <SpeciesView species={species} onSpecies={onSpecies} clusters={clusters} />;
}

export default function SpeciesPage() {
  return (
    <PublicShell>
      <Suspense>
        <Species />
      </Suspense>
    </PublicShell>
  );
}
