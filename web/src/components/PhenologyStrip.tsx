"use client";

import type { SpeciesPhenology } from "@/lib/api";
import { oceanRamp } from "@/lib/color";
import { COUNTRY_COLORS, MONTHS } from "@/lib/format";
import { useSize } from "@/lib/useSize";

const LABEL_W = 132;
const ROW = 15;
const TOP = 18;

/** Compact cluster × week heat strip shown beside the expanded time-lapse map. */
export function PhenologyStrip({
  data,
  mode,
  week,
  onWeek,
}: {
  data: SpeciesPhenology;
  mode: "shape" | "absolute";
  week: number | null;
  onWeek: (w: number) => void;
}) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const cw = Math.max(2, (width - LABEL_W) / 53);
  const height = TOP + data.groups.length * ROW + 4;
  const globalMax = Math.max(1e-9, ...data.groups.filter((g) => !g.sparse).map((g) => g.peak_rate));

  return (
    <div ref={ref} className="w-full">
      {width > 0 && (
        <svg
          width={width}
          height={height}
          className="cursor-pointer select-none"
          onClick={(e) => {
            const x = e.clientX - e.currentTarget.getBoundingClientRect().left - LABEL_W;
            if (x >= 0) onWeek(Math.min(53, Math.max(1, Math.floor(x / cw) + 1)));
          }}
        >
          <defs>
            <pattern id="strip-hatch" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="3" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
            </pattern>
          </defs>
          {MONTHS.map((m, i) => (
            <text key={m} x={LABEL_W + ((i * 365) / 12 / 7) * cw + 1} y={11} fontSize={9} fill="rgba(255,255,255,0.4)">
              {m}
            </text>
          ))}
          {data.groups.map((g, gi) => {
            const y = TOP + gi * ROW;
            const max = mode === "shape" ? Math.max(1e-9, g.peak_rate) : globalMax;
            return (
              <g key={g.id} opacity={g.sparse ? 0.35 : 1}>
                <rect x={0} y={y + 3} width={2.5} height={ROW - 6} fill={COUNTRY_COLORS[g.country ?? ""] ?? "#fff"} />
                <text x={6} y={y + ROW - 4} fontSize={10.5} fill="rgba(255,255,255,0.75)">
                  {g.label.length > 19 ? `${g.label.slice(0, 18)}…` : g.label}
                </text>
                {g.weeks.map((w) => (
                  <rect
                    key={w.week}
                    x={LABEL_W + (w.week - 1) * cw}
                    y={y}
                    width={cw - 0.5}
                    height={ROW - 1.5}
                    fill={
                      w.low_effort || w.rate === null
                        ? "url(#strip-hatch)"
                        : w.rate === 0
                          ? "#0c1d2a"
                          : oceanRamp(Math.min(1, Math.sqrt(w.rate / max)))
                    }
                  />
                ))}
              </g>
            );
          })}
          {week && (
            <rect
              x={LABEL_W + (week - 1) * cw - 1}
              y={TOP - 3}
              width={cw + 1}
              height={height - TOP + 1}
              fill="none"
              stroke="#f4b860"
              strokeWidth={1.5}
              rx={2}
            />
          )}
        </svg>
      )}
    </div>
  );
}
