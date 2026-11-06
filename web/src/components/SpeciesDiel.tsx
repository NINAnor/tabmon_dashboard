"use client";

import { scaleLinear } from "d3-scale";
import { area, curveMonotoneX, line } from "d3-shape";
import { useState } from "react";
import useSWR from "swr";
import { fetcher, qs } from "@/lib/api";
import { COUNTRY_COLORS, pct, rate } from "@/lib/format";
import { useSize } from "@/lib/useSize";
import { Segmented } from "./Controls";
import { DielClock } from "./DielClock";

export type SpeciesDiel = {
  overall: (number | null)[];
  countries: Record<string, (number | null)[]>;
  grid: (number | null)[][];
  peak_hour: number | null;
  night_share: number | null;
};

const H = 220;
const PAD = { l: 40, r: 12, t: 14, b: 26 };
const NIGHT: [number, number][] = [
  [0, 4],
  [23, 24],
];

function AverageDay({ data, byCountry }: { data: SpeciesDiel; byCountry: boolean }) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const series: [string, (number | null)[], string][] = byCountry
    ? Object.entries(data.countries).map(([c, v]) => [c, v, COUNTRY_COLORS[c] ?? "#fff"])
    : [["All countries", data.overall, "#4ecdc4"]];
  const max = Math.max(1e-9, ...series.flatMap(([, v]) => v.map((x) => x ?? 0)));
  const x = scaleLinear().domain([0, 23]).range([PAD.l, Math.max(PAD.l + 10, width - PAD.r)]);
  const y = scaleLinear().domain([0, max]).nice().range([H - PAD.b, PAD.t]);
  const pts = (v: (number | null)[]) => v.map((r, h) => [h, r] as [number, number | null]);
  const defined = (d: [number, number | null]) => d[1] !== null;

  return (
    <div ref={ref} className="relative">
      {width > 0 && (
        <svg
          width={width}
          height={H}
          onMouseMove={(e) => {
            const px = e.clientX - e.currentTarget.getBoundingClientRect().left;
            setHover(Math.min(23, Math.max(0, Math.round(x.invert(px)))));
          }}
          onMouseLeave={() => setHover(null)}
        >
          {NIGHT.map(([a, b]) => (
            <rect
              key={a}
              x={x(Math.max(0, a - 0.5))}
              width={x(Math.min(23, b - 0.5)) - x(Math.max(0, a - 0.5))}
              y={PAD.t}
              height={H - PAD.b - PAD.t}
              fill="rgba(120,140,255,0.07)"
            />
          ))}
          {y.ticks(4).map((t) => (
            <g key={t}>
              <line x1={PAD.l} x2={width - PAD.r} y1={y(t)} y2={y(t)} stroke="rgba(255,255,255,0.06)" />
              <text x={PAD.l - 6} y={y(t) + 3} fontSize={10} textAnchor="end" fill="rgba(255,255,255,0.4)">
                {rate(t)}
              </text>
            </g>
          ))}
          {[0, 3, 6, 9, 12, 15, 18, 21].map((h) => (
            <text key={h} x={x(h)} y={H - 8} fontSize={10} textAnchor="middle" fill="rgba(255,255,255,0.45)">
              {String(h).padStart(2, "0")}:00
            </text>
          ))}
          {!byCountry && (
            <path
              d={
                area<[number, number | null]>()
                  .defined(defined)
                  .x((d) => x(d[0]))
                  .y0(H - PAD.b)
                  .y1((d) => y(d[1] ?? 0))
                  .curve(curveMonotoneX)(pts(data.overall)) ?? ""
              }
              fill="rgba(78,205,196,0.18)"
            />
          )}
          {series.map(([name, v, color]) => (
            <path
              key={name}
              d={
                line<[number, number | null]>()
                  .defined(defined)
                  .x((d) => x(d[0]))
                  .y((d) => y(d[1] ?? 0))
                  .curve(curveMonotoneX)(pts(v)) ?? ""
              }
              fill="none"
              stroke={color}
              strokeWidth={2}
            />
          ))}
          {!byCountry && data.peak_hour !== null && data.overall[data.peak_hour] !== null && (
            <g>
              <circle cx={x(data.peak_hour)} cy={y(data.overall[data.peak_hour]!)} r={4} fill="#f4b860" />
              <text
                x={x(data.peak_hour)}
                y={y(data.overall[data.peak_hour]!) - 9}
                fontSize={10}
                textAnchor="middle"
                fill="#f4b860"
              >
                peak {String(data.peak_hour).padStart(2, "0")}:00
              </text>
            </g>
          )}
          {hover !== null && (
            <line x1={x(hover)} x2={x(hover)} y1={PAD.t} y2={H - PAD.b} stroke="rgba(255,255,255,0.3)" />
          )}
        </svg>
      )}
      {hover !== null && (
        <div className="tooltip" style={{ left: Math.min(x(hover) + 12, width - 170), top: 10 }}>
          <div className="font-medium text-white">
            {String(hover).padStart(2, "0")}:00–{String(hover + 1).padStart(2, "0")}:00
          </div>
          {series.map(([name, v, color]) => (
            <div key={name} className="flex justify-between gap-4">
              <span style={{ color }}>{name}</span>
              <span className="tabular-nums">{rate(v[hover])}</span>
            </div>
          ))}
          <div className="mt-1 text-white/40">detections per recorded hour</div>
        </div>
      )}
    </div>
  );
}

export function SpeciesDielPanel({ species, year }: { species: string; year: number | null }) {
  const [view, setView] = useState<"all" | "country">("all");
  const { data } = useSWR<SpeciesDiel>(`/api/public/phenology/diel${qs({ species, year })}`, fetcher, {
    keepPreviousData: true,
  });

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
      <div className="card p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="eyebrow">An average day</p>
            <p className="mt-1 text-sm text-white/55">
              Detections per recorded hour by time of day (local time). Shaded: night (23:00–04:00).
              {data?.night_share !== null && data?.night_share !== undefined && (
                <> {pct(data.night_share, 0)} of activity is at night.</>
              )}
            </p>
          </div>
          <Segmented
            options={[
              ["all", "All countries"],
              ["country", "By country"],
            ]}
            value={view}
            onChange={setView}
          />
        </div>
        {data ? <AverageDay data={data} byCountry={view === "country"} /> : <div className="h-56 animate-pulse rounded-xl bg-white/5" />}
        {view === "country" && data && (
          <div className="mt-2 flex flex-wrap gap-4 text-xs text-white/60">
            {Object.keys(data.countries).map((c) => (
              <span key={c} className="flex items-center gap-1.5">
                <span className="h-0.5 w-4 rounded" style={{ background: COUNTRY_COLORS[c] }} /> {c}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="card flex flex-col items-center p-5">
        <div className="w-full">
          <p className="eyebrow">Through the year</p>
          <p className="mt-1 text-sm text-white/55">
            Hour of day around the dial, January (inside) to December (outside), all clusters.
          </p>
        </div>
        {data && <DielClock diel={data.grid} size={340} />}
      </div>
    </div>
  );
}
