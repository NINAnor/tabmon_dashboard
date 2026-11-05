"use client";

import useSWR from "swr";
import { fetcher, type Overview } from "@/lib/api";
import { compact, int } from "@/lib/format";
import { SpectrogramBackdrop } from "./SpectrogramBackdrop";

export function Hero() {
  const { data } = useSWR<Overview>("/api/public/overview", fetcher);

  const stats = [
    ["Recorders", data ? `${data.devices_online}/${data.devices}` : "–", "online now"],
    ["Hours recorded", data ? compact(data.hours_recorded) : "–", "of soundscape"],
    ["Detections", data ? compact(data.n_detections) : "–", "BirdNET, calibrated"],
    ["Species", data ? int(data.n_species) : "–", `across ${data?.countries ?? "–"} countries`],
  ];

  return (
    <section className="relative flex min-h-[92vh] items-end overflow-hidden pt-16">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#123044_0%,_#07131c_55%)]" />
      <SpectrogramBackdrop />
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-ocean-900 to-transparent" />

      <div className="relative mx-auto w-full max-w-7xl px-6 pb-20">
        <p className="eyebrow mb-5">Transnational acoustic biodiversity monitoring</p>
        <h1 className="max-w-4xl font-serif text-5xl leading-[1.05] md:text-7xl">
          Listening to Europe&rsquo;s birds,
          <br />
          <span className="italic text-teal">from Spain to the Arctic.</span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-white/65">
          A network of autonomous recorders across {data?.clusters ?? "30"} landscapes in Spain, France,
          the Netherlands and Norway. Every few minutes they listen &mdash; and together they reveal when
          birds arrive, sing and leave.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a href="#phenology" className="rounded-full bg-teal px-5 py-2.5 text-sm font-medium text-ocean-950 hover:bg-teal/90">
            Follow the migration →
          </a>
          <a href="#places" className="rounded-full border border-white/30 px-5 py-2.5 text-sm hover:bg-white/10">
            Explore a place
          </a>
        </div>

        <dl className="mt-16 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-4">
          {stats.map(([label, value, sub]) => (
            <div key={label} className="bg-ocean-900/80 px-6 py-5 backdrop-blur">
              <dt className="eyebrow">{label}</dt>
              <dd className="mt-2 font-serif text-3xl tabular-nums md:text-4xl">{value}</dd>
              <dd className="mt-1 text-xs text-white/45">{sub}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
