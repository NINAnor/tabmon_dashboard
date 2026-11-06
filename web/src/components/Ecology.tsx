"use client";

import { BookOpen } from "lucide-react";
import type { Ecology } from "@/lib/api";

const IUCN_STYLE: Record<string, string> = {
  LC: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  NT: "bg-lime-400/15 text-lime-200 border-lime-300/30",
  VU: "bg-amber/15 text-amber border-amber/40",
  EN: "bg-orange-500/20 text-orange-300 border-orange-400/40",
  CR: "bg-coral/20 text-coral border-coral/40",
  DD: "bg-white/10 text-white/60 border-white/20",
};

export function IucnBadge({ ecology }: { ecology: Ecology | null }) {
  if (!ecology?.iucn) return null;
  return (
    <a
      href="https://www.iucnredlist.org/"
      target="_blank"
      rel="noreferrer"
      title={`Global IUCN Red List: ${ecology.iucn_label}`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        IUCN_STYLE[ecology.iucn] ?? IUCN_STYLE.DD
      }`}
    >
      <span className="font-bold">{ecology.iucn}</span> {ecology.iucn_label}
    </a>
  );
}

export function EcologyChips({ ecology }: { ecology: Ecology | null }) {
  if (!ecology) return null;
  const chips = [
    ecology.migration_label && { label: ecology.migration_label, strong: true },
    ...ecology.diet.slice(0, 2).map((d) => ({ label: d, strong: false })),
    ...ecology.habitats.slice(0, 3).map((h) => ({ label: h, strong: false })),
  ].filter(Boolean) as { label: string; strong: boolean }[];
  if (!chips.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {chips.map((c) => (
        <span
          key={c.label}
          className={`rounded-full px-2.5 py-0.5 text-[11px] ${
            c.strong ? "bg-teal/15 text-teal" : "bg-white/5 text-white/65"
          }`}
        >
          {c.label}
        </span>
      ))}
    </div>
  );
}

export function HowToRead({ ecology }: { ecology: Ecology | null }) {
  if (!ecology?.how_to_read.length) return null;
  return (
    <div className="rounded-xl border border-amber/20 bg-amber/[0.04] p-3">
      <p className="eyebrow mb-1.5 flex items-center gap-1.5 text-amber/80">
        <BookOpen className="h-3 w-3" /> How to read the chart
      </p>
      {ecology.how_to_read.map((p, i) => (
        <p key={i} className={`text-[13px] leading-relaxed text-white/75 ${i > 0 ? "mt-1.5" : ""}`}>
          {p}
        </p>
      ))}
      {ecology.trait_source && (
        <p className="mt-2 text-[10px] text-white/35">
          Traits: {ecology.trait_source} · Status: IUCN via Wikidata · Patterns: TABMON recordings
        </p>
      )}
    </div>
  );
}
