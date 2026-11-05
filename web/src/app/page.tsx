"use client";

import useSWR from "swr";
import { Hero } from "@/components/Hero";
import { NetworkOverview, useNetwork } from "@/components/NetworkOverview";
import { PublicShell } from "@/components/SiteHeader";
import { fetcher, type Cluster } from "@/lib/api";

export default function NetworkPage() {
  const { data: clusters = [] } = useSWR<Cluster[]>("/api/public/clusters", fetcher);
  const { data: network } = useNetwork();
  return (
    <PublicShell>
      <Hero validated={network?.pipeline.validated} />
      <NetworkOverview clusters={clusters} />
    </PublicShell>
  );
}
