"use client";

import { scaleLinear } from "d3-scale";
import { area, curveStepAfter, line } from "d3-shape";
import { useMemo, useState } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { compact, displayName, int, pct } from "@/lib/format";
import { useSize } from "@/lib/useSize";

type CurvePoint = {
  confidence: number;
  p_correct: number | null;
  p_lower: number | null;
  p_upper: number | null;
  n_validated_above: number;
  n_detections_above: number;
};

type ObservedBin = {
  confidence: number;
  n_validated: number;
  n_correct: number;
  p_lower: number | null;
  p_upper: number | null;
};

type Calibration = {
  species: string;
  common_en: string | null;
  threshold: number;
  threshold_lower: number | null;
  threshold_upper: number | null;
  threshold_method: string | null;
  threshold_source: string;
  n_validated: number;
  n_detections: number;
  target: number;
  fallback: number;
  curve: CurvePoint[];
  observed: ObservedBin[];
};

const H = 250;
const HIST_H = 42;
const M = { top: 14, right: 16, bottom: 30, left: 44 };
const BIN = 0.05;

export function CalibrationPanel({ species }: { species: string }) {
  const { data } = useSWR<Calibration>(`/api/public/species/${encodeURIComponent(species)}/calibration`, fetcher);
  if (!data || data.curve.length === 0) return null;
  return (
    <div id="calibration" className="card scroll-mt-32 p-5 md:scroll-mt-20">
      <p className="eyebrow">How reliable is BirdNET for the {displayName(data)}?</p>
      <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_320px]">
        <CalibrationChart data={data} />
        <Explanation data={data} />
      </div>
    </div>
  );
}

function CalibrationChart({ data }: { data: Calibration }) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const [hover, setHover] = useState<CurvePoint | null>(null);
  const plotW = Math.max(0, width - M.left - M.right);
  const calibrated = data.threshold_source === "calibrated" || data.threshold_source === "calibrated_low";
  const level = data.threshold_source === "calibrated_low" ? data.fallback : data.target;

  const x = useMemo(() => scaleLinear().domain([0.1, 1]).range([M.left, M.left + plotW]), [plotW]);
  const y = useMemo(() => scaleLinear().domain([0, 1]).range([M.top + H, M.top]), []);

  // Detections per 0.01 score bin, from the cumulative counts above each score.
  const hist = useMemo(
    () =>
      data.curve.map((c, i) => ({
        confidence: c.confidence,
        n: c.n_detections_above - (data.curve[i + 1]?.n_detections_above ?? 0),
      })),
    [data.curve],
  );
  const histY = scaleLinear()
    .domain([0, Math.max(1, ...hist.map((h) => h.n))])
    .range([0, HIST_H]);
  const histTop = M.top + H + M.bottom + 18;

  const fitted = data.curve.filter((c) => c.p_correct !== null);
  const curvePath =
    line<CurvePoint>()
      .x((c) => x(c.confidence))
      .y((c) => y(c.p_correct!))(fitted) ?? "";
  const bandPath =
    area<CurvePoint>()
      .defined((c) => c.p_lower !== null && c.p_upper !== null)
      .x((c) => x(c.confidence))
      .y0((c) => y(c.p_lower!))
      .y1((c) => y(c.p_upper!))(data.curve) ?? "";
  const histPath =
    area<{ confidence: number; n: number }>()
      .curve(curveStepAfter)
      .x((h) => x(h.confidence))
      .y0(histTop + HIST_H)
      .y1((h) => histTop + HIST_H - histY(h.n))(hist) ?? "";

  const tx = x(data.threshold);
  const tLo = data.threshold_lower !== null ? x(data.threshold_lower) : null;
  const tHi = x(data.threshold_upper ?? 1);
  const totalH = histTop + HIST_H + 18;

  return (
    <div ref={ref} className="relative">
      {width > 0 && (
        <svg
          width={width}
          height={totalH}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const c = x.invert(e.clientX - rect.left);
            const nearest = data.curve.reduce((a, b) => (Math.abs(b.confidence - c) < Math.abs(a.confidence - c) ? b : a));
            setHover(c >= 0.1 && c <= 1 ? nearest : null);
          }}
          onMouseLeave={() => setHover(null)}
        >
          {/* Grid and axes */}
          {[0, 0.25, 0.5, 0.75, 1].map((v) => (
            <g key={v}>
              <line x1={M.left} x2={M.left + plotW} y1={y(v)} y2={y(v)} stroke="rgba(255,255,255,0.07)" />
              <text x={M.left - 8} y={y(v)} dy="0.32em" textAnchor="end" className="fill-white/40 text-[10px]">
                {v * 100}%
              </text>
            </g>
          ))}
          {[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1].map((v) => (
            <text key={v} x={x(v)} y={M.top + H + 16} textAnchor="middle" className="fill-white/40 text-[10px]">
              {v.toFixed(1)}
            </text>
          ))}
          <text x={M.left + plotW} y={M.top + H + 28} textAnchor="end" className="fill-white/35 text-[10px]">
            BirdNET confidence →
          </text>
          <text x={M.left} y={M.top - 4} className="fill-white/35 text-[10px]">
            Chance a detection is correct
          </text>

          {/* Threshold and its uncertainty */}
          {calibrated && (
            <>
              {tLo !== null && (
                <rect x={tLo} y={M.top} width={Math.max(1, tHi - tLo)} height={H} fill="rgba(78,205,196,0.07)" />
              )}
              <line x1={tx} x2={tx} y1={M.top} y2={histTop + HIST_H} stroke="#4ecdc4" strokeWidth={1.5} />
              <text x={tx + 5} y={M.top + 10} className="fill-teal text-[11px] font-medium">
                threshold {data.threshold.toFixed(2)}
              </text>
            </>
          )}

          {/* Target levels */}
          <line x1={M.left} x2={M.left + plotW} y1={y(data.target)} y2={y(data.target)} stroke="#ff7a6b" strokeDasharray="4 4" opacity={0.7} />
          <text x={M.left + plotW - 4} y={y(data.target) + 12} textAnchor="end" className="fill-coral text-[10px]">
            {pct(data.target, 0)} target
          </text>
          {level !== data.target && (
            <>
              <line x1={M.left} x2={M.left + plotW} y1={y(level)} y2={y(level)} stroke="#f4b860" strokeDasharray="2 4" opacity={0.6} />
              <text x={M.left + plotW - 4} y={y(level) + 12} textAnchor="end" className="fill-amber text-[10px]">
                {pct(level, 0)} fallback
              </text>
            </>
          )}

          {/* Fitted curve with its 95% band */}
          <path d={bandPath} fill="rgba(244,184,96,0.18)" />
          <path d={curvePath} fill="none" stroke="#f4b860" strokeWidth={2.2} />

          {/* Observed share correct per 0.05 bin, with 95% intervals */}
          {data.observed.map((o) => {
            const cx = x(o.confidence);
            return (
              <g key={o.confidence}>
                {o.p_lower !== null && o.p_upper !== null && (
                  <>
                    <line x1={cx} x2={cx} y1={y(o.p_lower)} y2={y(o.p_upper)} stroke="rgba(255,255,255,0.55)" />
                    <line x1={cx - 3} x2={cx + 3} y1={y(o.p_lower)} y2={y(o.p_lower)} stroke="rgba(255,255,255,0.55)" />
                    <line x1={cx - 3} x2={cx + 3} y1={y(o.p_upper)} y2={y(o.p_upper)} stroke="rgba(255,255,255,0.55)" />
                  </>
                )}
                <circle cx={cx} cy={y(o.n_correct / o.n_validated)} r={3.5} fill="#fff" fillOpacity={0.85}>
                  <title>
                    {`${(o.confidence - BIN / 2).toFixed(2)}–${(o.confidence + BIN / 2).toFixed(2)}: ${o.n_correct} of ${o.n_validated} checked clips correct (95% interval ${pct(o.p_lower, 0)}–${pct(o.p_upper, 0)})`}
                  </title>
                </circle>
              </g>
            );
          })}

          {/* Distribution of all detections */}
          <path d={histPath} fill="rgba(127,184,255,0.35)" />
          <text x={M.left} y={histTop - 4} className="fill-white/40 text-[10px]">
            All BirdNET detections by confidence
          </text>

          {hover && (
            <line x1={x(hover.confidence)} x2={x(hover.confidence)} y1={M.top} y2={histTop + HIST_H} stroke="rgba(255,255,255,0.35)" />
          )}
        </svg>
      )}
      {hover && (
        <div
          className="pointer-events-none absolute z-10 w-56 rounded-lg border border-white/10 bg-ocean-950/95 p-3 text-xs shadow-xl"
          style={{ left: Math.min(x(hover.confidence) + 12, width - 232), top: M.top + 20 }}
        >
          <p className="font-medium">BirdNET confidence {hover.confidence.toFixed(2)}</p>
          {hover.p_correct !== null && (
            <p className="mt-1 text-amber">
              {pct(hover.p_correct, 0)} chance a detection is correct
              {hover.p_lower !== null && hover.p_upper !== null && (
                <span className="text-white/45">
                  {" "}
                  ({pct(hover.p_lower, 0)}–{pct(hover.p_upper, 0)})
                </span>
              )}
            </p>
          )}
          <p className="mt-1 text-white/50">
            {compact(hover.n_detections_above)} detections at or above · {int(hover.n_validated_above)} checked
          </p>
        </div>
      )}
    </div>
  );
}

function Explanation({ data }: { data: Calibration }) {
  const total = data.curve[0]?.n_detections_above ?? 0;
  const kept = data.curve.find((c) => Math.abs(c.confidence - data.threshold) < 0.001)?.n_detections_above;
  const range =
    data.threshold_lower !== null
      ? data.threshold_upper !== null
        ? ` (95% range ${data.threshold_lower.toFixed(2)}–${data.threshold_upper.toFixed(2)})`
        : ` (95% range from ${data.threshold_lower.toFixed(2)} upwards)`
      : "";
  return (
    <div className="space-y-3 text-sm text-white/65">
      <p>
        <span className="text-white">{int(data.curve[0]?.n_validated_above)} clips</span> scoring 0.10 or more were checked
        by experts and volunteers, spread evenly across BirdNET&rsquo;s confidence scores. Each dot is the share that were correct in a 0.05-wide score
        band, with its 95% interval: long bars mean few checks.
      </p>
      <p>
        The <span className="text-amber">curve</span> is a logistic regression of correctness on the score
        {data.threshold_method === "logistic_ceiling" ? ", allowing accuracy to level off below 100%" : ""}; the band shows
        its uncertainty.
      </p>
      <p>
        {data.threshold_source === "calibrated" ? (
          <>
            Following the BirdNET guidelines, the threshold is the score where a detection has a{" "}
            {pct(data.target, 0)} chance of being correct: <span className="text-white">{data.threshold.toFixed(2)}</span>
            {range}. Only detections at or above it are counted: {compact(kept)} of {compact(total)}.
          </>
        ) : data.threshold_source === "calibrated_low" ? (
          <>
            The curve never reaches {pct(data.target, 0)}, so the threshold is where it reaches {pct(data.fallback, 0)}:{" "}
            <span className="text-white">{data.threshold.toFixed(2)}</span>
            {range}, keeping {compact(kept)} of {compact(total)} detections. Treat patterns with caution.
          </>
        ) : (
          <>The curve never reaches {pct(data.fallback, 0)}, so this species is not shown in the charts.</>
        )}
      </p>
    </div>
  );
}
