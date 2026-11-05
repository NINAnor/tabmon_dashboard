"use client";

import { scaleLinear } from "d3-scale";
import { AudioLines, CheckCircle2, Mic, SlidersHorizontal } from "lucide-react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { fetcher, type Cluster } from "@/lib/api";
import { COUNTRY_COLORS, compact, int } from "@/lib/format";
import { useSize } from "@/lib/useSize";
import { ClusterMap } from "./ClusterMap";

export type Network = {
  countries: {
    country: string;
    n_clusters: number;
    n_sites: number;
    hours: number;
    n_species: number;
    top_species: string | null;
  }[];
  monthly: { country: string; month: string; hours: number }[];
  pipeline: {
    detections: number;
    validated: number;
    calibrated: number;
    species: number;
    files: number | null;
  };
};

export function useNetwork() {
  return useSWR<Network>("/api/public/network", fetcher);
}

function MonthlyHours({ rows }: { rows: Network["monthly"] }) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const months = [...new Set(rows.map((r) => r.month))].sort();
  const countries = Object.keys(COUNTRY_COLORS);
  const totals = months.map((m) => rows.filter((r) => r.month === m).reduce((s, r) => s + r.hours, 0));
  const H = 120;
  const y = scaleLinear().domain([0, Math.max(1, ...totals)]).range([0, H - 18]);
  const bw = months.length ? width / months.length : 0;
  return (
    <div ref={ref}>
      <svg width={width} height={H}>
        {months.map((m, i) => {
          let acc = 0;
          return (
            <g key={m} transform={`translate(${i * bw},0)`}>
              {countries.map((c) => {
                const v = rows.find((r) => r.month === m && r.country === c)?.hours ?? 0;
                const h = y(v);
                acc += h;
                return (
                  <rect key={c} x={0.5} width={Math.max(1, bw - 1.5)} y={H - 16 - acc} height={h} fill={COUNTRY_COLORS[c]} opacity={0.85}>
                    <title>{`${c} · ${m}: ${int(v)} h`}</title>
                  </rect>
                );
              })}
              {m.endsWith("-01") && (
                <text x={0} y={H - 3} fontSize={9} fill="rgba(255,255,255,0.45)">
                  {m.slice(0, 4)}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function NetworkOverview({ clusters }: { clusters: Cluster[] }) {
  const router = useRouter();
  const { data } = useNetwork();
  const maxHours = Math.max(1, ...(data?.countries ?? []).map((c) => c.hours));

  return (
    <section className="mx-auto max-w-7xl px-6 py-12">
      <div className="grid gap-6 lg:grid-cols-[3fr_2fr]">
        <div>
          <ClusterMap
            clusters={clusters}
            height={520}
            onSelect={(id) => router.push(`/sites?id=${encodeURIComponent(id)}`)}
          />
          <p className="mt-2 text-xs text-white/40">Click a landscape to explore its soundscape.</p>
        </div>

        <div className="flex flex-col gap-4">
          <div className="card p-5">
            <p className="eyebrow mb-4">The network by country</p>
            <ul className="space-y-4">
              {data?.countries.map((c) => (
                <li key={c.country}>
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="font-serif text-lg" style={{ color: COUNTRY_COLORS[c.country] }}>
                      {c.country}
                    </span>
                    <span className="text-xs tabular-nums text-white/55">
                      {c.n_clusters} landscapes · {c.n_sites} sites · {compact(c.hours)} h · {c.n_species} species
                    </span>
                  </div>
                  <div className="mt-1.5 h-1.5 rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${(c.hours / maxHours) * 100}%`, background: COUNTRY_COLORS[c.country] }}
                    />
                  </div>
                  {c.top_species && (
                    <p className="mt-1 text-[11px] text-white/40">Most detected: {c.top_species}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
          <div className="card p-5">
            <p className="eyebrow mb-3">Hours analysed per month</p>
            {data ? <MonthlyHours rows={data.monthly} /> : <div className="h-28 animate-pulse rounded bg-white/5" />}
          </div>
        </div>
      </div>

      <HowItWorks pipeline={data?.pipeline} />
    </section>
  );
}

function HowItWorks({ pipeline }: { pipeline?: Network["pipeline"] }) {
  const steps = [
    {
      icon: Mic,
      title: "Record",
      value: pipeline?.files ? `${compact(pipeline.files)} files` : "–",
      text: "Solar-powered recorders save 5 minutes of sound at a time, day and night, and upload it over mobile data.",
    },
    {
      icon: AudioLines,
      title: "Detect",
      value: pipeline ? `${compact(pipeline.detections)} detections` : "–",
      text: "BirdNET, a neural network trained on bird sounds, scans every 3 seconds of audio for species.",
    },
    {
      icon: CheckCircle2,
      title: "Validate",
      value: pipeline ? `${compact(pipeline.validated)} clips checked` : "–",
      text: "Experts and citizen scientists listen to samples and confirm or reject BirdNET's suggestions.",
    },
    {
      icon: SlidersHorizontal,
      title: "Calibrate",
      value: pipeline ? `${pipeline.calibrated} species calibrated` : "–",
      text: "Validations set a reliable confidence threshold per species; detections are counted per hour of recording.",
    },
  ];
  return (
    <div className="mt-10">
      <p className="eyebrow mb-4">How it works</p>
      <ol className="grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-4">
        {steps.map((s, i) => (
          <li key={s.title} className="bg-ocean-900 p-5">
            <div className="flex items-center gap-2 text-teal">
              <s.icon className="h-4 w-4" />
              <span className="text-xs text-white/40">{i + 1}</span>
              <span className="font-serif text-lg text-white">{s.title}</span>
            </div>
            <p className="mt-2 font-serif text-xl tabular-nums text-amber">{s.value}</p>
            <p className="mt-1 text-sm text-white/55">{s.text}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
