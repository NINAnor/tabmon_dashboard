"use client";

import { useState } from "react";
import useSWR from "swr";
import { fetcher, qs, type Cluster, type SpeciesPhenology } from "@/lib/api";
import { displayName, weekLabel } from "@/lib/format";
import { ClipList } from "./ClipPlayer";
import { ClusterMap } from "./ClusterMap";
import { Segmented, YearToggle } from "./Controls";
import { Ridgeline, RidgelineLegend } from "./Ridgeline";
import { SpeciesCard } from "./SpeciesCard";
import { SpeciesPicker, useSpeciesList } from "./SpeciesPicker";

export function PhenologySection({ clusters }: { clusters: Cluster[] }) {
  const [species, setSpecies] = useState("Cuculus canorus");
  const [year, setYear] = useState<number | null>(2025);
  const [mode, setMode] = useState<"shape" | "absolute">("shape");
  const [selected, setSelected] = useState<string | null>(null);
  const { data: list } = useSpeciesList();
  const { data, isLoading, error } = useSWR<SpeciesPhenology>(
    `/api/public/phenology/species${qs({ species, year, level: "cluster" })}`,
    fetcher,
    { keepPreviousData: true },
  );
  const row = list?.find((s) => s.species === species);
  const sel = data?.groups.find((g) => g.id === selected);
  const detected = data?.groups.filter((g) => g.total > 0 && g.median_week && !g.sparse) ?? [];
  const south = detected.at(-1);
  const north = detected[0];

  return (
    <section id="phenology" className="mx-auto max-w-7xl scroll-mt-20 px-6 py-24">
      <p className="eyebrow">When does it arrive where?</p>
      <h2 className="mt-3 max-w-3xl font-serif text-4xl md:text-5xl">
        Follow the season as it moves north.
      </h2>
      <p className="mt-4 max-w-2xl text-white/60">
        Each ridge is one landscape, ordered from Arctic Norway at the top to the Ebro Delta at the bottom.
        Height shows how often the species is detected per hour of recording, so gaps in recording do not look
        like absences.
      </p>

      <div className="mt-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <SpeciesPicker value={species} onChange={(s) => { setSpecies(s); setSelected(null); }} />
        <div className="flex flex-wrap gap-3">
          <YearToggle years={data?.years ?? []} value={year} onChange={setYear} />
          <Segmented
            options={[["shape", "Seasonal shape"], ["absolute", "Absolute activity"]]}
            value={mode}
            onChange={setMode}
          />
        </div>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_380px]">
        <div className="card p-5">
          <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
            <h3 className="font-serif text-2xl">
              {row ? displayName(row) : species} <span className="text-base italic text-white/40">{species}</span>
            </h3>
            {data && north && south && north.median_week && south.median_week && north !== south && (
              <p className="text-sm text-white/60">
                Mid-season{" "}
                <b className="text-amber">{weekLabel(data.week_starts, south.median_week)}</b> in {south.label} →{" "}
                <b className="text-amber">{weekLabel(data.week_starts, north.median_week)}</b> in {north.label}
              </p>
            )}
          </div>
          {error && <p className="text-coral">Could not load phenology.</p>}
          {isLoading && !data && <div className="h-[900px] animate-pulse rounded-xl bg-white/5" />}
          {data && (
            <div className={isLoading ? "opacity-60 transition-opacity" : "transition-opacity"}>
              <Ridgeline data={data} mode={mode} selected={selected} onSelect={(g) => setSelected(g.id)} />
            </div>
          )}
          <div className="mt-3">
            <RidgelineLegend />
          </div>
        </div>

        <div className="flex flex-col gap-6">
          <ClusterMap
            clusters={clusters}
            phenology={data}
            selected={selected}
            onSelect={setSelected}
            height={380}
          />
          <SpeciesCard species={species} compactView />
          <ClipList
            species={species}
            clusterId={selected}
            title={sel ? `Listen · ${sel.label}` : "Listen"}
            limit={4}
          />
        </div>
      </div>
    </section>
  );
}
