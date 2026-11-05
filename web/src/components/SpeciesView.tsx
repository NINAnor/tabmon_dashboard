"use client";

import { ArrowRight, Shuffle } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { fetcher, qs, type Cluster, type SpeciesPhenology } from "@/lib/api";
import { weekLabel } from "@/lib/format";
import { ClipList } from "./ClipPlayer";
import { ClusterMap } from "./ClusterMap";
import { Segmented, YearToggle } from "./Controls";
import { MigrationSpeed } from "./MigrationSpeed";
import { PhenologyStrip } from "./PhenologyStrip";
import { Ridgeline, RidgelineLegend } from "./Ridgeline";
import { SpeciesHeader, SpeciesHowToRead, SpeciesStats } from "./SpeciesCard";
import { pickRandomSpecies, SpeciesPicker, useSpeciesList } from "./SpeciesPicker";
import { TimeLapse } from "./TimeLapse";

export function SpeciesView({
  species,
  onSpecies,
  clusters,
}: {
  species: string | null;
  onSpecies: (species: string) => void;
  clusters: Cluster[];
}) {
  const { data: list } = useSpeciesList();
  const [year, setYear] = useState<number | null>(2025);
  const [mode, setMode] = useState<"shape" | "absolute">("shape");
  const [selected, setSelected] = useState<string | null>(null);
  const [week, setWeek] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);

  // No species in the URL: open on a random validated one.
  useEffect(() => {
    if (!species && list?.length) {
      const pick = pickRandomSpecies(list);
      if (pick) onSpecies(pick);
    }
  }, [list, species, onSpecies]);

  useEffect(() => {
    setSelected(null);
    setWeek(null);
    setPlaying(false);
  }, [species]);

  const { data, isLoading, error } = useSWR<SpeciesPhenology>(
    species ? `/api/public/phenology/species${qs({ species, year, level: "cluster" })}` : null,
    fetcher,
    { keepPreviousData: true },
  );
  const sel = data?.groups.find((g) => g.id === selected);
  const detected = data?.groups.filter((g) => g.total > 0 && g.median_week && !g.sparse) ?? [];
  const south = detected.at(-1);
  const north = detected[0];
  const expanded = week !== null && !!data;
  const expandedRef = useRef<HTMLDivElement>(null);
  const wasExpanded = useRef(false);
  // Bring the large map into view when the time-lapse starts.
  useEffect(() => {
    if (expanded && !wasExpanded.current) {
      expandedRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    wasExpanded.current = expanded;
  }, [expanded]);

  const controls = (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <TimeLapse week={week} onWeek={setWeek} playing={playing} onPlaying={setPlaying} weekStarts={data?.week_starts ?? []} />
      {data && north && south && north.median_week && south.median_week && north !== south && (
        <p className="text-sm text-white/60">
          Mid-season <b className="text-amber">{weekLabel(data.week_starts, south.median_week)}</b> in {south.label} →{" "}
          <b className="text-amber">{weekLabel(data.week_starts, north.median_week)}</b> in {north.label}
        </p>
      )}
    </div>
  );

  return (
    <section className="mx-auto max-w-7xl px-6 py-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-2">
          <SpeciesPicker value={species} onChange={onSpecies} />
          <button
            className="pill mt-1.5 shrink-0"
            title="Random validated species"
            onClick={() => {
              const pick = list && pickRandomSpecies(list.filter((s) => s.species !== species));
              if (pick) onSpecies(pick);
            }}
          >
            <Shuffle className="h-3.5 w-3.5" /> Surprise me
          </button>
        </div>
        <div className="flex flex-wrap gap-3">
          <YearToggle years={data?.years ?? []} value={year} onChange={setYear} />
          <Segmented
            options={[
              ["shape", "Seasonal shape"],
              ["absolute", "Absolute activity"],
            ]}
            value={mode}
            onChange={setMode}
          />
        </div>
      </div>

      {species && (
        <div className="mt-6">
          <SpeciesHeader species={species} />
        </div>
      )}

      <div className="mt-6">
        {expanded ? (
          <div ref={expandedRef} className="card scroll-mt-20 p-5">
            {controls}
            <div className="grid gap-5 lg:grid-cols-[3fr_2fr]">
              <ClusterMap
                clusters={clusters}
                phenology={data}
                selected={selected}
                onSelect={setSelected}
                height="68vh"
                week={week}
                mode={mode}
                large
              />
              <div className="flex flex-col gap-3">
                <p className="eyebrow">Activity by landscape · north to south · click to jump</p>
                <PhenologyStrip
                  data={data!}
                  mode={mode}
                  week={week}
                  onWeek={(w) => {
                    setPlaying(false);
                    setWeek(w);
                  }}
                />
                <p className="text-xs text-white/45">
                  {mode === "shape"
                    ? "Each landscape is scaled to its own peak, so quiet northern sites still light up on arrival."
                    : "One scale for all landscapes: compare absolute calling rates."}{" "}
                  Switch with “Seasonal shape / Absolute activity” above.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
            <div className="card p-5">
              <p className="eyebrow mb-1">When does it arrive where?</p>
              <p className="mb-4 text-sm text-white/55">
                One ridge per landscape, from Arctic Norway (top) to the Ebro Delta (bottom). Height is detections per
                hour of recording. Press play to watch the season sweep across a large map.
              </p>
              {controls}
              {error && <p className="text-coral">Could not load phenology.</p>}
              {!data && <div className="h-[900px] animate-pulse rounded-xl bg-white/5" />}
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
              {species && <SpeciesHowToRead species={species} />}
              <ClusterMap clusters={clusters} phenology={data} selected={selected} onSelect={setSelected} height={340} mode={mode} />
              {sel && (
                <Link
                  href={`/sites?id=${encodeURIComponent(sel.id)}`}
                  className="-mt-3 flex items-center gap-1 text-sm text-teal hover:underline"
                >
                  Open {sel.label} in Sites <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              )}
              {data && <MigrationSpeed migration={data.migration} species={species} />}
            </div>
          </div>
        )}
      </div>

      {species && (
        <>
          <div className="mt-6">
            <SpeciesStats species={species} />
          </div>
          <div className="mt-6">
            <ClipList species={species} clusterId={selected} title={sel ? `Listen · ${sel.label}` : "Listen"} limit={6} />
          </div>
        </>
      )}
    </section>
  );
}
