"use client";

import { scaleLinear } from "d3-scale";
import { useState } from "react";
import type { PlaceProfile } from "@/lib/api";
import { oceanRamp } from "@/lib/color";
import { MONTHS, displayName, rate, weekLabel } from "@/lib/format";
import { useSize } from "@/lib/useSize";

const LABEL_W = 200;
const ROW = 19;
const EFFORT_H = 26;

export function SeasonalGrid({
  data,
  selected,
  onSelect,
}: {
  data: PlaceProfile;
  selected: string | null;
  onSelect: (species: string | null) => void;
}) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const [hover, setHover] = useState<{ s: number; w: number; x: number; y: number } | null>(null);
  const plotW = Math.max(200, width - LABEL_W - 8);
  const cw = plotW / 53;
  const top = EFFORT_H + 22;
  const height = top + data.species.length * ROW + 4;
  const effortMax = Math.max(1, ...data.effort_weeks);
  const ey = scaleLinear().domain([0, effortMax]).range([0, EFFORT_H - 4]);

  return (
    <div ref={ref} className="relative">
      {width > 0 && (
        <svg width={width} height={height} onMouseLeave={() => setHover(null)}>
          <defs>
            <pattern id="grid-hatch" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="4" stroke="rgba(255,255,255,0.12)" strokeWidth="1" />
            </pattern>
          </defs>
          <text x={LABEL_W - 10} y={EFFORT_H - 6} textAnchor="end" fontSize={10} fill="rgba(255,255,255,0.4)">
            Hours recorded
          </text>
          {data.effort_weeks.map((m, i) => (
            <rect
              key={i}
              x={LABEL_W + i * cw + 0.5}
              y={EFFORT_H - ey(m)}
              width={Math.max(1, cw - 1)}
              height={ey(m)}
              fill="rgba(255,255,255,0.18)"
            />
          ))}
          {MONTHS.map((m, i) => {
            const week = 1 + (i * 365) / 12 / 7;
            return (
              <text key={m} x={LABEL_W + (week - 1) * cw + 2} y={top - 6} fontSize={10} fill="rgba(255,255,255,0.45)">
                {m}
              </text>
            );
          })}
          {data.species.map((s, si) => {
            const max = Math.max(1e-9, ...s.cells.map((c) => c ?? 0));
            const y = top + si * ROW;
            const isSel = selected === s.species;
            return (
              <g
                key={s.species}
                className="cursor-pointer"
                onClick={() => onSelect(isSel ? null : s.species)}
              >
                <rect x={0} y={y} width={LABEL_W - 4} height={ROW - 2} fill={isSel ? "rgba(78,205,196,0.15)" : "transparent"} rx={4} />
                <text
                  x={LABEL_W - 10}
                  y={y + ROW / 2 + 3}
                  textAnchor="end"
                  fontSize={11.5}
                  fill={isSel ? "#4ecdc4" : "rgba(255,255,255,0.8)"}
                >
                  {displayName(s).slice(0, 28)}
                </text>
                {s.cells.map((c, wi) => (
                  <rect
                    key={wi}
                    x={LABEL_W + wi * cw}
                    y={y}
                    width={cw - 1}
                    height={ROW - 2}
                    rx={1.5}
                    fill={c === null ? "url(#grid-hatch)" : c === 0 ? "#0c1d2a" : oceanRamp(Math.sqrt(c / max))}
                    onMouseEnter={(e) => {
                      const r = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect();
                      setHover({ s: si, w: wi, x: e.clientX - r.left, y: e.clientY - r.top });
                    }}
                  />
                ))}
              </g>
            );
          })}
        </svg>
      )}
      {hover && (
        <div className="tooltip" style={{ left: Math.min(hover.x + 12, width - 200), top: hover.y + 14, width: 190 }}>
          <div className="font-medium text-white">{displayName(data.species[hover.s])}</div>
          <div className="text-white/50">Week of {weekLabel(data.week_starts, hover.w + 1)}</div>
          <div className="mt-1">
            {data.species[hover.s].cells[hover.w] === null ? (
              <span className="text-amber">Too little recording</span>
            ) : (
              <>
                <span className="text-teal">{rate(data.species[hover.s].cells[hover.w])}</span> detections / hour
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
