"use client";

import { area, curveBasis, line } from "d3-shape";
import { scaleLinear, scaleSqrt } from "d3-scale";
import { useMemo, useState } from "react";
import type { PhenologyGroup, SpeciesPhenology } from "@/lib/api";
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
};

export function Ridgeline({ data, mode, selected, onSelect }: Props) {
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

  const medianPoints = groups
    .map((g, i) => (g.median_week && g.total > 0 && !g.sparse ? ([x(g.median_week), TOP + (i + 1) * ROW] as [number, number]) : null))
    .filter(Boolean) as [number, number][];

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
                  <text x={LABEL_W + plotW - 4} y={base - 4} textAnchor="end" fontSize={10} fill="rgba(255,255,255,0.3)">
                    few detections
                  </text>
                )}
                {g.first_week && !empty && !faint && (
                  <circle cx={x(g.first_week)} cy={base} r={3.2} fill="#f4b860" stroke="#07131c" strokeWidth={1.5} />
                )}
              </g>
            );
          })}

          {medianPoints.length > 1 && (
            <path
              d={line().curve(curveBasis)(medianPoints) ?? ""}
              fill="none"
              stroke="#f4b860"
              strokeDasharray="3 4"
              strokeWidth={1.5}
              opacity={0.75}
              pointerEvents="none"
            />
          )}
          {medianPoints.map(([px, py], i) => (
            <line key={i} x1={px} x2={px} y1={py - 7} y2={py + 3} stroke="#f4b860" strokeWidth={2} pointerEvents="none" />
          ))}

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

export function RidgelineLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-white/55">
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full bg-amber" /> Arrival (10% of peak)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-3 w-0.5 bg-amber" /> Mid-season (50% of activity)
      </span>
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
    </div>
  );
}
