"use client";

import { useSpeciesList } from "./SpeciesPicker";
import { SpeciesCard } from "./SpeciesCard";

export function SpeciesSection() {
  const { data } = useSpeciesList();
  // Most-detected species that have been checked by validators.
  const top = (data ?? []).filter((s) => s.threshold_source !== "default").slice(0, 6);

  return (
    <section id="species" className="mx-auto max-w-7xl scroll-mt-20 px-6 py-24">
      <p className="eyebrow">Species</p>
      <h2 className="mt-3 max-w-3xl font-serif text-4xl md:text-5xl">The voices we hear most.</h2>
      <p className="mt-4 max-w-2xl text-white/60">
        Detections come from BirdNET. For every species shown here, experts and citizen scientists have listened
        to samples, and we only count detections above the confidence level where they were found reliable.
      </p>
      <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {top.map((s) => (
          <SpeciesCard key={s.species} species={s.species} compactView />
        ))}
      </div>
    </section>
  );
}
