"use client";

import useSWR from "swr";
import { Hero } from "@/components/Hero";
import { PhenologySection } from "@/components/PhenologySection";
import { PlacesSection } from "@/components/PlaceExplorer";
import { Footer, SiteHeader } from "@/components/SiteHeader";
import { SpeciesSection } from "@/components/SpeciesSection";
import { fetcher, type Cluster } from "@/lib/api";

export default function Home() {
  const { data: clusters = [] } = useSWR<Cluster[]>("/api/public/clusters", fetcher);
  return (
    <>
      <SiteHeader />
      <main>
        <Hero />
        <PhenologySection clusters={clusters} />
        {clusters.length > 0 && <PlacesSection clusters={clusters} />}
        <SpeciesSection />
      </main>
      <Footer />
    </>
  );
}
