"use client";

import { scaleLinear } from "d3-scale";
import { Navigation } from "lucide-react";
import useSWR from "swr";
import { fetcher, type Migration, type SpeciesDetail } from "@/lib/api";
import { MONTHS } from "@/lib/format";

function dayLabel(day: number) {
  const d = new Date(Date.UTC(2025, 0, 1) + (day - 1) * 864e5);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`;
}

const NO_WAVE: Record<string, string> = {
  resident: "As a resident species, it is present all year, so no arrival wave is expected.",
  partial: "As a partial migrant, many birds stay all year, which blurs any arrival wave.",
  short_distance: "Short-distance migrants winter nearby, so arrival is spread out and hard to time.",
  long_distance: "Long-distance migrant, but detections are too uneven across landscapes to time arrival.",
};

export function MigrationSpeed({ migration, species }: { migration: Migration; species?: string | null }) {
  const { data: detail } = useSWR<SpeciesDetail>(
    species ? `/api/public/species/${encodeURIComponent(species)}` : null,
    fetcher,
  );
  const kind = detail?.ecology?.migration ?? "";
  const pts = migration.points ?? [];
  const W = 300;
  const H = 150;
  const pad = { l: 36, r: 10, t: 10, b: 24 };

  return (
    <div className="card p-5">
      <p className="eyebrow flex items-center gap-1.5">
        <Navigation className="h-3 w-3" /> Speed of the season
      </p>
      {migration.clear && migration.km_per_day ? (
        <>
          <p className="mt-2 font-serif text-3xl">
            ≈ {Math.round(migration.km_per_day)} <span className="text-lg text-white/60">km / day</span>
          </p>
          <p className="text-xs text-white/50">
            Mid-season arrives {migration.days_per_degree!.toFixed(1)} days later per degree north · fit across{" "}
            {migration.n} landscapes (R² {migration.r2!.toFixed(2)})
          </p>
        </>
      ) : (
        <p className="mt-2 text-sm text-white/60">
          No clear northward wave{migration.reason ? ` (${migration.reason})` : ""}.{" "}
          {NO_WAVE[kind] ?? "Typical of residents or species with few detections."}
        </p>
      )}

      {pts.length >= 3 && (() => {
        const x = scaleLinear()
          .domain([Math.min(...pts.map((p) => p.day)) - 7, Math.max(...pts.map((p) => p.day)) + 7])
          .range([pad.l, W - pad.r]);
        const y = scaleLinear()
          .domain([Math.min(...pts.map((p) => p.lat)) - 1, Math.max(...pts.map((p) => p.lat)) + 1])
          .range([H - pad.b, pad.t]);
        const [lat0, lat1] = y.domain();
        const line =
          migration.days_per_degree !== undefined && migration.intercept !== undefined
            ? [lat0, lat1].map((lat) => [x(migration.intercept! + migration.days_per_degree! * lat), y(lat)])
            : null;
        return (
          <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full">
            {y.ticks(4).map((t) => (
              <g key={t}>
                <line x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} stroke="rgba(255,255,255,0.06)" />
                <text x={pad.l - 6} y={y(t) + 3} fontSize={9} textAnchor="end" fill="rgba(255,255,255,0.4)">
                  {t}°N
                </text>
              </g>
            ))}
            {x.ticks(4).map((t) => (
              <text key={t} x={x(t)} y={H - 6} fontSize={9} textAnchor="middle" fill="rgba(255,255,255,0.4)">
                {dayLabel(t)}
              </text>
            ))}
            {line && migration.clear && (
              <line
                x1={line[0][0]}
                y1={line[0][1]}
                x2={line[1][0]}
                y2={line[1][1]}
                stroke="#f4b860"
                strokeDasharray="4 3"
                strokeWidth={1.5}
              />
            )}
            {pts.map((p, i) => (
              <circle key={i} cx={x(p.day)} cy={y(p.lat)} r={3.5} fill="#4ecdc4" stroke="#07131c" />
            ))}
          </svg>
        );
      })()}
    </div>
  );
}
