"use client";

import { AlertTriangle, CheckCircle2, Search } from "lucide-react";
import { useMemo, useState } from "react";
import useSWR from "swr";
import { fetcher, type SpeciesRow } from "@/lib/api";
import { compact, displayName, pct } from "@/lib/format";

const FEATURED = [
  "Cuculus canorus",
  "Hirundo rustica",
  "Phylloscopus trochilus",
  "Phylloscopus collybita",
  "Apus apus",
  "Ficedula hypoleuca",
  "Sylvia atricapilla",
  "Erithacus rubecula",
];

export function useSpeciesList() {
  return useSWR<SpeciesRow[]>("/api/public/species?limit=500", fetcher);
}

/** Random calibrated species with enough data for an interesting first view. */
export function pickRandomSpecies(list: SpeciesRow[]): string | null {
  const good = list.filter((s) => s.calibrated && s.n_sites >= 10 && s.n_detections >= 5000);
  const pool = good.length ? good : list.filter((s) => s.calibrated);
  if (!pool.length) return list[0]?.species ?? null;
  return pool[Math.floor(Math.random() * pool.length)].species;
}

function Row({ s, onPick }: { s: SpeciesRow; onPick: () => void }) {
  return (
    <li>
      <button
        className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-white/5"
        onMouseDown={onPick}
      >
        <span className="flex min-w-0 items-center gap-2">
          {s.calibrated ? (
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-teal" />
          ) : (
            <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-coral/60" aria-label="Not yet validated" />
          )}
          <span className="truncate">
            {displayName(s)} <span className="italic text-white/40">{s.species}</span>
          </span>
        </span>
        <span className="shrink-0 text-xs tabular-nums text-white/40">
          {s.calibrated && s.precision_at_threshold !== null
            ? `${pct(s.precision_at_threshold, 0)} precise`
            : compact(s.n_detections)}
        </span>
      </button>
    </li>
  );
}

export function SpeciesPicker({
  value,
  onChange,
}: {
  value: string | null;
  onChange: (species: string) => void;
}) {
  const { data = [] } = useSpeciesList();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);

  const featured = FEATURED.map((s) => data.find((d) => d.species === s)).filter(Boolean) as SpeciesRow[];
  const validated = useMemo(() => data.filter((d) => d.calibrated), [data]);
  const matches = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return [];
    return data
      .filter((d) => d.species.toLowerCase().includes(needle) || (d.common_en ?? "").toLowerCase().includes(needle))
      .slice(0, 30);
  }, [q, data]);

  const pick = (species: string) => {
    onChange(species);
    setQ("");
    setOpen(false);
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-white/40" />
        <input
          className="input pl-9"
          placeholder={`Search ${data.length || ""} species…`}
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
        {open && (
          <ul className="absolute z-40 mt-1 max-h-96 w-full overflow-auto rounded-xl border border-white/15 bg-ocean-950/95 py-1 shadow-2xl backdrop-blur">
            {q.trim() ? (
              matches.length ? (
                matches.map((s) => <Row key={s.species} s={s} onPick={() => pick(s.species)} />)
              ) : (
                <li className="px-3 py-2 text-sm text-white/40">No species found</li>
              )
            ) : (
              <>
                <li className="eyebrow px-3 pb-1 pt-2">
                  Validated by experts &amp; citizens · {validated.length}
                </li>
                {validated.map((s) => (
                  <Row key={s.species} s={s} onPick={() => pick(s.species)} />
                ))}
                <li className="px-3 py-2 text-xs text-white/40">
                  Type to search all {data.length} species ·{" "}
                  <AlertTriangle className="inline h-3 w-3 text-coral/60" /> = not yet validated, treat with caution
                </li>
              </>
            )}
          </ul>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {featured.map((s) => (
          <button
            key={s.species}
            className={`pill ${value === s.species ? "pill-active" : ""}`}
            onClick={() => onChange(s.species)}
          >
            {displayName(s)}
          </button>
        ))}
      </div>
    </div>
  );
}
