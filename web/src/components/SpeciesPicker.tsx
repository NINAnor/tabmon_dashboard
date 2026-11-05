"use client";

import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import useSWR from "swr";
import { fetcher, type SpeciesRow } from "@/lib/api";
import { compact, displayName } from "@/lib/format";

export const FEATURED = [
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

export function SpeciesPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (species: string) => void;
}) {
  const { data = [] } = useSpeciesList();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);

  const featured = FEATURED.map((s) => data.find((d) => d.species === s)).filter(Boolean) as SpeciesRow[];
  const matches = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return data.slice(0, 12);
    return data
      .filter((d) => d.species.toLowerCase().includes(needle) || (d.common_en ?? "").toLowerCase().includes(needle))
      .slice(0, 12);
  }, [q, data]);

  return (
    <div className="flex flex-col gap-3">
      <div className="relative max-w-md">
        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-white/40" />
        <input
          className="input pl-9"
          placeholder="Search a species…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
        {open && matches.length > 0 && (
          <ul className="absolute z-40 mt-1 max-h-80 w-full overflow-auto rounded-xl border border-white/15 bg-ocean-950/95 py-1 shadow-2xl">
            {matches.map((s) => (
              <li key={s.species}>
                <button
                  className="flex w-full items-baseline justify-between gap-3 px-3 py-2 text-left text-sm hover:bg-white/5"
                  onMouseDown={() => {
                    onChange(s.species);
                    setQ("");
                    setOpen(false);
                  }}
                >
                  <span>
                    {displayName(s)} <span className="italic text-white/40">{s.species}</span>
                  </span>
                  <span className="text-xs tabular-nums text-white/40">{compact(s.n_detections)}</span>
                </button>
              </li>
            ))}
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
