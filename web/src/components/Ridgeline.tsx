"use client";

import { area, curveBasis, line } from "d3-shape";
import { scaleLinear, scaleSqrt } from "d3-scale";
import { useMemo, useState } from "react";
import type { MigrationFit, PhenologyGroup, SpeciesPhenology } from "@/lib/api";
import { COUNTRY_COLORS, MONTHS, int, rate, weekLabel } from "@/lib/format";
import { useSize } from "@/lib/useSize";

const ROW = 30;
const LABEL_W = 190;
const TOP = 34;
const RIGHT = 16;

type Props = {
  data: SpeciesPhenology;
  mode: "shape" | "absolute";
  selected?: string | null;
  onSelect?: (group: PhenologyGroup) => void;
  /** Week highlighted by the time-lapse. */
  cursorWeek?: number | null;
};

export function Ridgeline({ data, mode, selected, onSelect, cursorWeek }: Props) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const [hover, setHover] = useState<{ g: PhenologyGroup; week: number; x: number; y: number } | null>(
    null,
  );

  const groups = data.groups;
  const height = TOP + groups.length * ROW + 30;
  const plotW = Math.max(200, width - LABEL_W - RIGHT);

  const x = useMemo(() => scaleLinear().domain([1, 53]).range([LABEL_W, LABEL_W + plotW]), [plotW]);
  const globalMax = Math.max(1e-9, ...groups.map((g) => g.peak_rate));
  const amp = ROW * 1.9;

  // Sparse rows (a handful of likely false positives) are drawn against at least
  // a quarter of the global peak so isolated detections do not look like seasons.
  const yScale = (g: PhenologyGroup) =>
    mode === "shape"
      ? scaleLinear()
          .domain([0, Math.max(1e-9, g.sparse ? Math.max(g.peak_rate, 0.25 * globalMax) : g.peak_rate)])
          .range([0, amp])
      : scaleSqrt().domain([0, globalMax]).range([0, amp]);

  const monthTicks = MONTHS.map((m, i) => {
    const y = data.year ?? 2025;
    const week = 1 + (Date.UTC(y, i, 1) - Date.UTC(y, 0, 1)) / (7 * 864e5);
    return { m, week };
  });

  // Only the clusters the API used for each fit (seasonal windows applied there).
  const wavePoints = (week: "onset_week" | "end_week", fit: MigrationFit) => {
    const ids = new Set((fit.points ?? []).map((p) => p.id));
    return groups
      .map((g, i) =>
        ids.has(g.id) && g[week] !== null
          ? ([x(g[week]!), TOP + (i + 1) * ROW] as [number, number])
          : null,
      )
      .filter((point): point is [number, number] => point !== null);
  };
  const { migration } = data;
  const springPoints = migration.show_waves && migration.spring.clear ? wavePoints("onset_week", migration.spring) : [];
  const autumnPoints = migration.show_waves && migration.autumn.clear ? wavePoints("end_week", migration.autumn) : [];

  let prevCountry: string | null = null;

  return (
    <div ref={ref} className="relative w-full">
      {width > 0 && (
        <svg
          width={width}
          height={height}
          className="block select-none"
          onMouseLeave={() => setHover(null)}
          onMouseMove={(e) => {
            const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
            const px = e.clientX - rect.left;
            const py = e.clientY - rect.top;
            const row = Math.floor((py - TOP + ROW * 0.2) / ROW);
            const g = groups[row];
            if (!g || px < LABEL_W) return setHover(null);
            const week = Math.min(53, Math.max(1, Math.round(x.invert(px))));
            setHover({ g, week, x: px, y: py });
          }}
        >
          <defs>
            <pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="5" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" />
            </pattern>
            <linearGradient id="ridge" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#4ecdc4" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#4ecdc4" stopOpacity="0.15" />
            </linearGradient>
          </defs>

          {monthTicks.map(({ m, week }) => (
            <g key={m}>
              <line x1={x(week)} x2={x(week)} y1={TOP - 8} y2={height - 24} stroke="rgba(255,255,255,0.06)" />
              <text x={x(week) + 4} y={TOP - 14} fill="rgba(255,255,255,0.45)" fontSize={11}>
                {m}
              </text>
            </g>
          ))}

          {groups.map((g, i) => {
            const base = TOP + (i + 1) * ROW;
            const y = yScale(g);
            const empty = g.total === 0;
            const faint = g.sparse && !empty;
            const path = area<(typeof g.weeks)[number]>()
              .defined((w) => !w.low_effort && w.rate !== null)
              .x((w) => x(w.week))
              .y0(base)
              .y1((w) => base - y(w.rate ?? 0))
              .curve(curveBasis)(g.weeks);
            const outline = line<(typeof g.weeks)[number]>()
              .defined((w) => !w.low_effort && w.rate !== null)
              .x((w) => x(w.week))
              .y((w) => base - y(w.rate ?? 0))
              .curve(curveBasis)(g.weeks);
            const newCountry = g.country !== prevCountry;
            prevCountry = g.country;
            const isSel = selected === g.id;
            return (
              <g
                key={g.id}
                className="cursor-pointer"
                onClick={() => onSelect?.(g)}
                opacity={selected && !isSel ? 0.55 : 1}
              >
                {newCountry && i > 0 && (
                  <line x1={8} x2={LABEL_W + plotW} y1={base - ROW + 6} y2={base - ROW + 6} stroke="rgba(255,255,255,0.12)" />
                )}
                {newCountry && (
                  <text x={8} y={base - ROW + 20} fontSize={10} letterSpacing={2} fill={COUNTRY_COLORS[g.country ?? ""] ?? "#fff"}>
                    {(g.country ?? "").toUpperCase()}
                  </text>
                )}
                {g.weeks.map((w) =>
                  w.low_effort ? (
                    <rect key={w.week} x={x(w.week - 0.5)} width={x(2) - x(1)} y={base - 5} height={5} fill="url(#hatch)" />
                  ) : null,
                )}
                {path && <path d={path} fill="url(#ridge)" opacity={empty ? 0 : faint ? 0.3 : 0.85} />}
                {outline && (
                  <path d={outline} fill="none" stroke="#a9f0eb" strokeWidth={isSel ? 2 : 1} opacity={empty ? 0 : faint ? 0.35 : 0.9} />
                )}
                <line x1={LABEL_W} x2={LABEL_W + plotW} y1={base} y2={base} stroke="rgba(255,255,255,0.15)" />
                <text
                  x={LABEL_W - 10}
                  y={base - 4}
                  textAnchor="end"
                  fontSize={12}
                  fill={empty || faint ? "rgba(255,255,255,0.35)" : isSel ? "#4ecdc4" : "rgba(255,255,255,0.85)"}
                >
                  {g.label.length > 22 ? `${g.label.slice(0, 21)}…` : g.label}
                </text>
                {empty && (
                  <text x={LABEL_W + 8} y={base - 4} fontSize={10} fill="rgba(255,255,255,0.3)">
                    not detected
                  </text>
                )}
                {faint && (
                  <text x={LABEL_W + plotW - 4} y={base - 4} textAnchor="end" fontSize={10} fill="rgba(255,255,255,0.4)">
                    few detections · {int(g.total)}
                    {g.peak_week !== null ? ` · peak ${weekLabel(data.week_starts, g.peak_week)}` : ""}
                  </text>
                )}
              </g>
            );
          })}

          {springPoints.length >= 3 && (
            <path
              d={line().curve(curveBasis)(springPoints) ?? ""}
              fill="none"
              stroke="#f4b860"
              strokeDasharray="3 4"
              strokeWidth={1.5}
              opacity={0.75}
              pointerEvents="none"
            />
          )}
          {autumnPoints.length >= 3 && (
            <path
              d={line().curve(curveBasis)(autumnPoints) ?? ""}
              fill="none"
              stroke="#ff7a6b"
              strokeDasharray="3 4"
              strokeWidth={1.5}
              opacity={0.75}
              pointerEvents="none"
            />
          )}
          {groups.map((g, i) => {
            if (g.total === 0) return null;
            const base = TOP + (i + 1) * ROW;
            return (
              <g key={g.id} pointerEvents="none" opacity={g.sparse ? 0.4 : 1}>
                {g.onset_week !== null && (
                  <circle cx={x(g.onset_week)} cy={base} r={3.2} fill="#f4b860" stroke="#07131c" strokeWidth={1.5} />
                )}
                {g.peak_week !== null && (
                  <line x1={x(g.peak_week)} x2={x(g.peak_week)} y1={base - 5} y2={base + 2} stroke="#f4f4f0" strokeWidth={2} />
                )}
                {g.end_week !== null && (
                  <circle cx={x(g.end_week)} cy={base} r={3.2} fill="#ff7a6b" stroke="#07131c" strokeWidth={1.5} />
                )}
              </g>
            );
          })}

          {cursorWeek && (
            <g pointerEvents="none">
              <rect
                x={x(cursorWeek - 0.5)}
                width={x(2) - x(1)}
                y={TOP - 6}
                height={height - 24 - TOP + 6}
                fill="rgba(244,184,96,0.12)"
              />
              <line x1={x(cursorWeek)} x2={x(cursorWeek)} y1={TOP - 6} y2={height - 24} stroke="#f4b860" strokeWidth={1.5} />
            </g>
          )}
          {hover && (
            <line
              x1={x(hover.week)}
              x2={x(hover.week)}
              y1={TOP - 6}
              y2={height - 24}
              stroke="rgba(255,255,255,0.35)"
              pointerEvents="none"
            />
          )}
        </svg>
      )}

      {hover && (() => {
        const w = hover.g.weeks[hover.week - 1];
        return (
          <div
            className="tooltip"
            style={{ left: Math.min(hover.x + 14, width - 220), top: hover.y + 12, width: 205 }}
          >
            <div className="font-medium text-white">{hover.g.label}</div>
            <div className="text-white/50">Week of {weekLabel(data.week_starts, hover.week)}</div>
            <div className="mt-1.5 flex justify-between">
              <span>Detections / hour</span>
              <span className="tabular-nums text-teal">{w.low_effort ? "–" : rate(w.rate)}</span>
            </div>
            <div className="flex justify-between">
              <span>Detections</span>
              <span className="tabular-nums">{int(w.n)}</span>
            </div>
            <div className="flex justify-between">
              <span>Hours recorded</span>
              <span className="tabular-nums">{int(w.minutes / 60)}</span>
            </div>
            {w.low_effort && <div className="mt-1 text-amber">Too little recording this week</div>}
          </div>
        );
      })()}
    </div>
  );
}

export function RidgelineLegend({ showWaves }: { showWaves: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-white/55">
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full bg-amber" /> Onset (10% of activity)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-3 w-0.5 bg-white/90" /> Peak
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full bg-coral" /> End (90% of activity)
      </span>
      {showWaves && (
        <>
          <span className="flex items-center gap-1.5">
            <span className="w-5 border-t border-dashed border-amber" /> Spring wave
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-5 border-t border-dashed border-coral" /> Autumn wave
          </span>
        </>
      )}
      <span className="flex items-center gap-1.5">
        <svg width="18" height="6">
          <rect width="18" height="6" fill="url(#hatch-legend)" />
          <defs>
            <pattern id="hatch-legend" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="4" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
            </pattern>
          </defs>
        </svg>
        Not enough recording
      </span>
      <span className="flex items-center gap-1.5 text-white/40">
        <span className="h-2 w-4 rounded-sm bg-teal/30" /> Faded: few detections
        {showWaves ? ", not used for the waves" : ""}
      </span>
    </div>
  );
}
