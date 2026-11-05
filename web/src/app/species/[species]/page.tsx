"use client";

import Link from "next/link";
import { use, useState } from "react";
import useSWR from "swr";
import { ClipList } from "@/components/ClipPlayer";
import { ClusterMap } from "@/components/ClusterMap";
import { Segmented, YearToggle } from "@/components/Controls";
import { Ridgeline, RidgelineLegend } from "@/components/Ridgeline";
import { Footer, SiteHeader } from "@/components/SiteHeader";
import { SpeciesCard } from "@/components/SpeciesCard";
import { fetcher, qs, type Cluster, type SpeciesPhenology } from "@/lib/api";
import { unslug } from "@/lib/format";

export default function SpeciesPage({ params }: { params: Promise<{ species: string }> }) {
  const species = unslug(use(params).species);
  const [year, setYear] = useState<number | null>(null);
  const [level, setLevel] = useState<"cluster" | "country">("cluster");
  const [selected, setSelected] = useState<string | null>(null);
  const { data: clusters = [] } = useSWR<Cluster[]>("/api/public/clusters", fetcher);
  const { data } = useSWR<SpeciesPhenology>(
    `/api/public/phenology/species${qs({ species, year, level })}`,
    fetcher,
    { keepPreviousData: true },
  );

  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-6 pb-24 pt-28">
        <Link href="/#species" className="text-sm text-teal hover:underline">
          ← All species
        </Link>
        <div className="mt-6 grid gap-6 lg:grid-cols-[380px_1fr]">
          <div className="flex flex-col gap-6">
            <SpeciesCard species={species} />
            <ClipList species={species} clusterId={level === "cluster" ? selected : null} limit={6} />
          </div>
          <div className="flex flex-col gap-6">
            <div className="card p-5">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <p className="eyebrow">Seasonal activity by latitude</p>
                <div className="flex flex-wrap gap-3">
                  <YearToggle years={data?.years ?? []} value={year} onChange={setYear} />
                  <Segmented
                    options={[["cluster", "Landscapes"], ["country", "Countries"]]}
                    value={level}
                    onChange={(v) => {
                      setLevel(v);
                      setSelected(null);
                    }}
                  />
                </div>
              </div>
              {data ? (
                <Ridgeline data={data} mode="shape" selected={selected} onSelect={(g) => setSelected(g.id)} />
              ) : (
                <div className="h-[700px] animate-pulse rounded-xl bg-white/5" />
              )}
              <div className="mt-3">
                <RidgelineLegend />
              </div>
            </div>
            {level === "cluster" && (
              <ClusterMap clusters={clusters} phenology={data} selected={selected} onSelect={setSelected} height={460} />
            )}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
