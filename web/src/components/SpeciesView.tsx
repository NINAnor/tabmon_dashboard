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
import { SpeciesDielPanel } from "./SpeciesDiel";
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
  const [year, setYear] = useState<number | null>(null);
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
  const detected = data?.groups.filter((g) => g.total > 0 && !g.sparse) ?? [];
  const springIds = new Set((data?.migration.spring.points ?? []).map((p) => p.id));
  const autumnIds = new Set((data?.migration.autumn.points ?? []).map((p) => p.id));
  const springGroups = detected.filter((g) => springIds.has(g.id) && g.onset_week !== null);
  const autumnGroups = detected.filter((g) => autumnIds.has(g.id) && g.end_week !== null);
  const springSouth = springGroups.at(-1);
  const springNorth = springGroups[0];
  const autumnNorth = autumnGroups[0];
  const autumnSouth = autumnGroups.at(-1);
  const peakGroup = detected
    .filter((g) => g.peak_week !== null)
    .reduce<(typeof detected)[number] | undefined>(
      (best, g) => (!best || g.total > best.total ? g : best),
      undefined,
    );
  const shapeTitle =
    "Each landscape scaled to its own peak: compare timing (when the season starts, peaks and ends), regardless of how common the species is.";
  const absoluteTitle =
    "One shared scale for all landscapes: compare how much the species is heard (detections per recorded hour).";
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

  const springClear = !!data?.migration.spring.clear;
  const autumnClear = !!data?.migration.autumn.clear;
  const controls = (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <TimeLapse week={week} onWeek={setWeek} playing={playing} onPlaying={setPlaying} weekStarts={data?.week_starts ?? []} />
      {data?.migration.show_waves && (springClear || autumnClear) ? (
        (springSouth || autumnNorth) && (
          <p className="text-sm text-white/60">
            {springClear && springSouth && springNorth && (
              <>
                Starts <b className="text-amber">{weekLabel(data.week_starts, springSouth.onset_week!)}</b> in {springSouth.label} →{" "}
                <b className="text-amber">{weekLabel(data.week_starts, springNorth.onset_week!)}</b> in {springNorth.label}
              </>
            )}
            {springClear && autumnClear && springSouth && autumnNorth && <span className="mx-2 text-white/35">·</span>}
            {autumnClear && autumnNorth && autumnSouth && (
              <>
                Falls silent <b className="text-coral">{weekLabel(data.week_starts, autumnNorth.end_week!)}</b> in {autumnNorth.label} →{" "}
                <b className="text-coral">{weekLabel(data.week_starts, autumnSouth.end_week!)}</b> in {autumnSouth.label}
              </>
            )}
          </p>
        )
      ) : (
        data && peakGroup?.peak_week !== null && peakGroup && (
          <p className="text-sm text-white/60">
            Peak activity <b className="text-amber">{weekLabel(data.week_starts, peakGroup.peak_week)}</b> ({peakGroup.label})
          </p>
        )
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
            titles={{ shape: shapeTitle, absolute: absoluteTitle }}
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
              <p className="eyebrow mb-1">When does its vocal season start and end?</p>
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
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                <RidgelineLegend showWaves={data?.migration.show_waves ?? false} />
                <p className="text-xs text-white/40">
                  {mode === "shape" ? shapeTitle : absoluteTitle}
                </p>
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
              {data && <MigrationSpeed data={data} />}
            </div>
          </div>
        )}
      </div>

      {species && (
        <>
          <div className="mt-6">
            <SpeciesDielPanel species={species} year={year} />
          </div>
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
