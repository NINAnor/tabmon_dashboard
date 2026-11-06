"use client";

import Link from "next/link";
import useSWR from "swr";
import { fetcher, type Overview } from "@/lib/api";
import { compact, int } from "@/lib/format";
import { SpectrogramBackdrop } from "./SpectrogramBackdrop";

export function Hero({ validated }: { validated?: number | null }) {
  const { data } = useSWR<Overview>("/api/public/overview", fetcher);

  const stats: [string, string, string][] = [
    ["Recorders", data ? `${data.devices_online}/${data.devices}` : "–", "online now"],
    ["Hours analysed", data ? compact(data.hours_recorded) : "–", "of soundscape"],
    ["Detections", data ? compact(data.n_detections) : "–", "BirdNET, calibrated"],
    ["Species", data ? int(data.n_species) : "–", `in ${data?.countries ?? "–"} countries`],
    ["Clips validated", validated ? compact(validated) : "–", "by experts & citizens"],
  ];

  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#123044_0%,_#07131c_60%)]" />
      <SpectrogramBackdrop />
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-ocean-900 to-transparent" />

      <div className="relative mx-auto w-full max-w-7xl px-6 pb-8 pt-12">
        <p className="eyebrow mb-3">Transnational acoustic biodiversity monitoring</p>
        <h1 className="max-w-4xl font-serif text-4xl leading-[1.08] md:text-5xl">
          Listening to Europe&rsquo;s birds, <span className="italic text-teal">from Spain to the Arctic.</span>
        </h1>
        <p className="mt-4 max-w-2xl text-white/65">
          Autonomous recorders in {data?.clusters ?? "–"} clusters across Spain, France, the Netherlands and
          Norway listen around the clock. Together they show when birds arrive, sing and leave.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/species" className="rounded-full bg-teal px-5 py-2.5 text-sm font-medium text-ocean-950 hover:bg-teal/90">
            Follow a species →
          </Link>
          <Link href="/sites" className="rounded-full border border-white/30 px-5 py-2.5 text-sm hover:bg-white/10">
            Explore a cluster
          </Link>
        </div>

        <dl className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-white/10 bg-white/10 md:grid-cols-5">
          {stats.map(([label, value, sub]) => (
            <div key={label} className="bg-ocean-900/80 px-5 py-3 backdrop-blur">
              <dt className="eyebrow">{label}</dt>
              <dd className="mt-1 flex items-baseline gap-2">
                <span className="font-serif text-2xl tabular-nums">{value}</span>
                <span className="text-[11px] text-white/45">{sub}</span>
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
