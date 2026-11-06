"use client";

import { scaleLinear } from "d3-scale";
import { Navigation } from "lucide-react";
import type { MigrationFit, SpeciesPhenology } from "@/lib/api";
import { MONTHS } from "@/lib/format";

const NO_WAVE: Record<string, string> = {
  resident: "present all year, so no arrival or departure wave is expected.",
  partial: "many birds stay all year, which blurs any arrival or departure wave.",
  short_distance: "short-distance migrants winter nearby, so arrival and departure are spread out.",
  long_distance: "detections are too uneven across clusters to time the waves.",
  migrant: "detections are too uneven across clusters to time the waves.",
};

const KIND_LABEL: Record<string, string> = {
  resident: "Resident species",
  partial: "Partial migrant",
  short_distance: "Short-distance migrant",
  long_distance: "Long-distance migrant",
  migrant: "Migrant",
};

function dateLabel(start: number, day: number) {
  const date = new Date(start + day * 864e5);
  return `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]}`;
}

function fitLine(fit: MigrationFit, fallbackLats: number[]) {
  if (
    !fit.clear ||
    typeof fit.days_per_degree !== "number" ||
    typeof fit.intercept !== "number"
  ) {
    return [] as { lat: number; day: number }[];
  }
  const lats = fit.points?.length ? fit.points.map((point) => point.lat) : fallbackLats;
  if (!lats.length) return [];
  const min = Math.min(...lats);
  const max = Math.max(...lats);
  return [min, max].map((lat) => ({
    lat,
    day: fit.intercept! + fit.days_per_degree! * lat,
  }));
}

function fitSummary(fit: MigrationFit) {
  return `${fit.n} clusters · R² ${typeof fit.r2 === "number" ? fit.r2.toFixed(2) : "–"}`;
}

export function MigrationSpeed({ data }: { data: SpeciesPhenology }) {
  const migration = data.migration;
  const springPoints = migration.spring.points ?? [];
  const autumnPoints = migration.autumn.points ?? [];
  const allPoints = [...springPoints, ...autumnPoints];
  const fallbackLats = allPoints.map((point) => point.lat);
  const springLine = fitLine(migration.spring, fallbackLats);
  const autumnLine = fitLine(migration.autumn, fallbackLats);
  const allLinePoints = [...springLine, ...autumnLine];
  const start = Date.parse(data.week_starts[data.season_start_week - 1] ?? "");
  const canChart = Number.isFinite(start) && allPoints.length > 0;
  const W = 360;
  const H = 180;
  const pad = { l: 38, r: 12, t: 10, b: 30 };

  return (
    <div className="card p-5">
      <p className="eyebrow flex items-center gap-1.5">
        <Navigation className="h-3 w-3" /> Spring &amp; autumn waves
      </p>
      {!migration.show_waves ? (
        <p className="mt-2 text-sm text-white/60">
          {migration.reason
            ? `${migration.reason.charAt(0).toUpperCase()}${migration.reason.slice(1)}: ${NO_WAVE[migration.kind ?? ""] ?? "no clear seasonal wave is expected."}`
            : `${KIND_LABEL[migration.kind ?? ""] ?? "Seasonal pattern"}: ${NO_WAVE[migration.kind ?? ""] ?? "no clear seasonal wave is expected."}`}
        </p>
      ) : (
        <>
          <div className="mt-2 space-y-2">
            <div>
              <p className="text-sm text-white/85">
                <span className="text-amber">Spring:</span>{" "}
                {migration.spring.clear && typeof migration.spring.km_per_day === "number" && typeof migration.spring.days_per_degree === "number"
                  ? `Season starts ≈ ${Math.round(migration.spring.km_per_day)} km/day northward (${migration.spring.days_per_degree.toFixed(1)} days later per degree north)`
                  : "No clear spring wave"}
              </p>
              <p className="text-[10px] text-white/40">{fitSummary(migration.spring)}</p>
            </div>
            <div>
              <p className="text-sm text-white/85">
                <span className="text-coral">Autumn:</span>{" "}
                {migration.autumn.clear && typeof migration.autumn.days_per_degree === "number"
                  ? `Falls silent ${Math.abs(migration.autumn.days_per_degree).toFixed(1)} days earlier per degree north`
                  : "No clear autumn wave"}
              </p>
              <p className="text-[10px] text-white/40">{fitSummary(migration.autumn)}</p>
            </div>
          </div>
          {canChart && (() => {
            const days = [...allPoints.map((point) => point.day), ...allLinePoints.map((point) => point.day)];
            const lats = [...allPoints.map((point) => point.lat), ...allLinePoints.map((point) => point.lat)];
            const dayMin = Math.min(...days);
            const dayMax = Math.max(...days);
            const latMin = Math.min(...lats);
            const latMax = Math.max(...lats);
            const x = scaleLinear()
              .domain(dayMin === dayMax ? [dayMin - 7, dayMax + 7] : [dayMin - 5, dayMax + 5])
              .range([pad.l, W - pad.r]);
            const y = scaleLinear()
              .domain([latMin - 1, latMax + 1])
              .range([H - pad.b, pad.t]);
            return (
              <svg viewBox={`0 0 ${W} ${H}`} className="mt-3 w-full" role="img" aria-label="Spring and autumn season dates by latitude">
                {y.ticks(4).map((tick) => (
                  <g key={tick}>
                    <line x1={pad.l} x2={W - pad.r} y1={y(tick)} y2={y(tick)} stroke="rgba(255,255,255,0.06)" />
                    <text x={pad.l - 6} y={y(tick) + 3} fontSize={9} textAnchor="end" fill="rgba(255,255,255,0.4)">
                      {tick}°N
                    </text>
                  </g>
                ))}
                {x.ticks(4).map((tick) => (
                  <text key={tick} x={x(tick)} y={H - 7} fontSize={9} textAnchor="middle" fill="rgba(255,255,255,0.4)">
                    {dateLabel(start, tick)}
                  </text>
                ))}
                {springLine.length === 2 && (
                  <line x1={x(springLine[0].day)} y1={y(springLine[0].lat)} x2={x(springLine[1].day)} y2={y(springLine[1].lat)} stroke="#f4b860" strokeDasharray="4 3" strokeWidth={1.5} />
                )}
                {autumnLine.length === 2 && (
                  <line x1={x(autumnLine[0].day)} y1={y(autumnLine[0].lat)} x2={x(autumnLine[1].day)} y2={y(autumnLine[1].lat)} stroke="#ff7a6b" strokeDasharray="4 3" strokeWidth={1.5} />
                )}
                {springPoints.map((point, i) => (
                  <circle key={`spring-${i}`} cx={x(point.day)} cy={y(point.lat)} r={3.5} fill="#f4b860" stroke="#07131c" />
                ))}
                {autumnPoints.map((point, i) => (
                  <circle key={`autumn-${i}`} cx={x(point.day)} cy={y(point.lat)} r={3.5} fill="#ff7a6b" stroke="#07131c" />
                ))}
              </svg>
            );
          })()}
          <p className="mt-2 text-[11px] text-white/45">
            Recordings show when birds fall silent, which can be weeks before they leave.
          </p>
        </>
      )}
    </div>
  );
}
