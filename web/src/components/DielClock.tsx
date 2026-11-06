"use client";

import { arc } from "d3-shape";
import { useState } from "react";
import { oceanRamp } from "@/lib/color";
import { MONTHS, rate } from "@/lib/format";

/**
 * Acoustic clock: hour of day around the circle, months as rings
 * (January inside, December outside). Colour = detections per recorded hour.
 */
export function DielClock({
  diel,
  size = 380,
  selectedMonth,
  onPickMonth,
}: {
  diel: (number | null)[][];
  size?: number;
  selectedMonth?: number | null;
  onPickMonth?: (month: number) => void;
}) {
  const [hover, setHover] = useState<{ m: number; h: number } | null>(null);
  const c = size / 2;
  const inner = size * 0.11;
  const outer = size * 0.39;
  const ringW = (outer - inner) / 12;
  const max = Math.max(1e-9, ...diel.flat().map((v) => v ?? 0));
  const seg = arc();

  const hv = hover ? diel[hover.m][hover.h] : null;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} onMouseLeave={() => setHover(null)}>
        <g transform={`translate(${c},${c})`}>
          {diel.map((row, m) =>
            row.map((v, h) => {
              const d = seg({
                innerRadius: inner + m * ringW,
                outerRadius: inner + (m + 1) * ringW - 0.8,
                startAngle: (h / 24) * 2 * Math.PI + 0.004,
                endAngle: ((h + 1) / 24) * 2 * Math.PI - 0.004,
              });
              const isSel = selectedMonth === m + 1;
              return (
                <path
                  key={`${m}-${h}`}
                  d={d ?? ""}
                  fill={v === null ? "rgba(255,255,255,0.03)" : v === 0 ? "#0c1d2a" : oceanRamp(Math.sqrt(v / max))}
                  stroke={isSel ? "rgba(244,184,96,0.9)" : "none"}
                  strokeWidth={isSel ? 0.8 : 0}
                  className="cursor-pointer"
                  onMouseEnter={() => setHover({ m, h })}
                  onClick={() => onPickMonth?.(m + 1)}
                />
              );
            }),
          )}
          {[0, 6, 12, 18].map((h) => {
            const a = (h / 24) * 2 * Math.PI;
            const r = outer + 14;
            return (
              <text
                key={h}
                x={Math.sin(a) * r}
                y={-Math.cos(a) * r + 4}
                textAnchor="middle"
                fontSize={11}
                fill="rgba(255,255,255,0.5)"
              >
                {String(h).padStart(2, "0")}:00
              </text>
            );
          })}
          <text textAnchor="middle" y={-4} fontSize={10} fill="rgba(255,255,255,0.45)">
            {hover ? MONTHS[hover.m] : "Jan"}
          </text>
          <text textAnchor="middle" y={10} fontSize={10} fill="rgba(255,255,255,0.45)">
            {hover ? `${String(hover.h).padStart(2, "0")}:00` : "inside"}
          </text>
        </g>
      </svg>
      {hover && (
        <div className="tooltip left-2 top-2">
          {MONTHS[hover.m]} · {String(hover.h).padStart(2, "0")}:00–{String(hover.h + 1).padStart(2, "0")}:00
          <div className="text-teal">{hv === null ? "Too little recording" : `${rate(hv)} detections / hour`}</div>
          {onPickMonth && <div className="text-white/40">Click to hear this month</div>}
        </div>
      )}
    </div>
  );
}
