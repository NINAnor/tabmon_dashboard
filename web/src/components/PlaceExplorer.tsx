"use client";

import { Headphones } from "lucide-react";
import Link from "next/link";
import { labLink } from "@/lib/lab";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { fetcher, qs, type Cluster, type PlaceProfile } from "@/lib/api";
import { compact, displayName, MONTHS, rate } from "@/lib/format";
import { ClipList } from "./ClipPlayer";
import { ClusterMap } from "./ClusterMap";
import { YearToggle } from "./Controls";
import { DielClock } from "./DielClock";
import { SeasonalGrid } from "./SeasonalGrid";

export function PlaceExplorer({
  level,
  id,
  title,
  subtitle,
  showClips = true,
}: {
  level: "cluster" | "site";
  id: string;
  title?: string;
  subtitle?: string;
  showClips?: boolean;
}) {
  const [year, setYear] = useState<number | null>(null);
  const [species, setSpecies] = useState<string | null>(null);
  const [month, setMonth] = useState<number | null>(null);

  useEffect(() => {
    setSpecies(null);
    setMonth(null);
  }, [id]);

  const { data, isLoading } = useSWR<PlaceProfile>(
    `/api/public/phenology/place${qs({ id, level, year, species, top: 25 })}`,
    fetcher,
    { keepPreviousData: true },
  );
  const selected = data?.species.find((s) => s.species === species);

  return (
    <div className="card p-5">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          {title && <h3 className="font-serif text-3xl">{title}</h3>}
          {subtitle && <p className="text-sm text-white/50">{subtitle}</p>}
        </div>
        <YearToggle years={data?.years ?? []} value={year} onChange={setYear} />
      </div>

      <div className="flex flex-col gap-10">
        <div className={isLoading ? "opacity-60" : ""}>
          <p className="eyebrow mb-2">Seasonal calendar · top species · click a row</p>
          {data && data.species.length > 0 ? (
            <SeasonalGrid data={data} selected={species} onSelect={setSpecies} />
          ) : (
            <div className="h-80 animate-pulse rounded-xl bg-white/5" />
          )}
        </div>
        <div className="grid items-start gap-8 lg:grid-cols-[400px_1fr]">
          <div className="flex flex-col gap-3">
            <div className="w-full">
            <p className="eyebrow">Acoustic clock</p>
            <p className="mt-1 text-sm text-white/60">
              {selected ? displayName(selected) : "All species together"} · hour of day around the dial, months
              from January (inside) to December (outside)
            </p>
            {selected && level === "cluster" && (
              <Link
                href={`/species?species=${encodeURIComponent(selected.species)}`}
                className="mt-1 inline-block text-sm text-teal hover:underline"
              >
                Open {displayName(selected)} in Species →
              </Link>
            )}
          </div>
            {data && <DielClock diel={data.diel} selectedMonth={month} onPickMonth={setMonth} />}
          </div>
          {showClips && level === "cluster" && (
            <div className="w-full">
              <ClipList
                clusterId={id}
                species={species}
                month={month}
                limit={4}
                title={`Listen${selected ? ` · ${displayName(selected)}` : ""}${month ? ` · ${MONTHS[month - 1]}` : ""}`}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

type TopSpecies = {
  species: string;
  common_en: string | null;
  n: number;
  rate: number | null;
  iucn: string | null;
  migration: string | null;
  calibrated: boolean;
};

const IUCN_DOT: Record<string, string> = {
  NT: "bg-lime-300",
  VU: "bg-amber",
  EN: "bg-orange-400",
  CR: "bg-coral",
};

function TopSpeciesList({ clusterId }: { clusterId: string }) {
  const { data } = useSWR<TopSpecies[]>(`/api/public/clusters/${encodeURIComponent(clusterId)}/species?limit=12`, fetcher);
  const max = Math.max(1e-9, ...(data ?? []).map((s) => s.rate ?? 0));
  return (
    <div className="card p-4">
      <p className="eyebrow mb-3">Most heard here · detections per hour</p>
      {!data && <div className="h-60 animate-pulse rounded bg-white/5" />}
      <ul className="space-y-1">
        {data?.map((s) => (
          <li key={s.species}>
            <Link
              href={`/species?species=${encodeURIComponent(s.species)}`}
              className="group flex items-center gap-2 rounded-lg px-1.5 py-1 text-sm hover:bg-white/5"
              title={s.iucn ? `IUCN: ${s.iucn}` : undefined}
            >
              <span className="w-32 truncate group-hover:text-teal">{displayName(s)}</span>
              {s.iucn && IUCN_DOT[s.iucn] && (
                <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${IUCN_DOT[s.iucn]}`} title={`IUCN ${s.iucn}`} />
              )}
              <span className="h-1.5 flex-1 rounded-full bg-white/5">
                <span className="block h-full rounded-full bg-teal/70" style={{ width: `${((s.rate ?? 0) / max) * 100}%` }} />
              </span>
              <span className="w-10 text-right text-xs tabular-nums text-white/50">{rate(s.rate)}</span>
            </Link>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-[10px] text-white/35">Coloured dots: near threatened or worse on the IUCN Red List.</p>
    </div>
  );
}

export function PlacesView({
  clusters,
  id,
  onChange,
}: {
  clusters: Cluster[];
  id: string | null;
  onChange: (id: string) => void;
}) {
  const cluster = clusters.find((c) => c.id === id) ?? clusters.find((c) => c.id === "norway-lillehammer") ?? clusters[0];

  return (
    <section className="mx-auto max-w-7xl px-6 py-10">
      <p className="eyebrow">What does this place sound like?</p>
      <h1 className="mt-2 font-serif text-4xl">A year of sound, landscape by landscape.</h1>
      <p className="mt-3 max-w-2xl text-white/60">
        Pick a landscape. The calendar shows which species are active each week; the clock shows when in the day
        they sing, from the dawn chorus to night-calling owls and migrants.
      </p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[340px_1fr]">
        <div className="flex flex-col gap-4">
          <ClusterMap clusters={clusters} selected={cluster?.id} onSelect={onChange} height={360} />
          <select className="input" value={cluster?.id} onChange={(e) => onChange(e.target.value)}>
            {clusters.map((c) => (
              <option key={c.id} value={c.id}>
                {c.country} · {c.label}
              </option>
            ))}
          </select>
          {cluster && (
            <dl className="grid grid-cols-3 gap-2 text-center">
              {[
                ["Species", cluster.n_species],
                ["Hours", compact(cluster.hours)],
                ["Sites", cluster.n_sites],
              ].map(([k, v]) => (
                <div key={k} className="card py-3">
                  <dt className="eyebrow">{k}</dt>
                  <dd className="mt-1 font-serif text-2xl">{v}</dd>
                </div>
              ))}
            </dl>
          )}
          {cluster?.habitats && (
            <div className="flex flex-wrap gap-1.5">
              {cluster.habitats.map((h) => (
                <span key={h} className="rounded-full bg-white/5 px-2.5 py-1 text-xs text-white/60">
                  {h}
                </span>
              ))}
            </div>
          )}
          {cluster && <TopSpeciesList clusterId={cluster.id} />}
          {cluster && (
            <a
              href={labLink({ country: cluster.country, cluster: cluster.label })}
              target="_blank"
              rel="noreferrer"
              className="card flex items-center gap-3 border-amber/30 p-4 hover:bg-amber/[0.06]"
            >
              <Headphones className="h-5 w-5 shrink-0 text-amber" />
              <span className="text-sm">
                <span className="text-amber">Listen to recordings from {cluster.label}</span>
                <span className="block text-xs text-white/50">
                  Help confirm what BirdNET heard here in the Listening Lab →
                </span>
              </span>
            </a>
          )}
        </div>
        {cluster && <PlaceExplorer level="cluster" id={cluster.id} title={cluster.label} subtitle={cluster.country} />}
      </div>
    </section>
  );
}
