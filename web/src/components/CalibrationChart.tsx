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
  p_logistic: number | null;
  precision_above: number | null;
  naive_precision_above: number | null;
  n_validated_above: number;
  n_detections_above: number;
};

type Calibration = {
  species: string;
  common_en: string | null;
  threshold: number;
  threshold_source: string;
  precision_at_threshold: number | null;
  n_validated: number;
  method: "logistic" | "empirical" | null;
  target: number;
  curve: CurvePoint[];
  observed: { confidence: number; n_validated: number; n_correct: number }[];
};

const H = 260;
const HIST_H = 46;
const M = { top: 14, right: 16, bottom: 30, left: 44 };

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

  const x = useMemo(() => scaleLinear().domain([0.1, 1]).range([M.left, M.left + plotW]), [plotW]);
  const y = useMemo(() => scaleLinear().domain([0, 1]).range([M.top + H, M.top]), []);

  // Detections per 0.01 score bin, from the cumulative counts above each threshold.
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
  const radius = scaleLinear()
    .domain([0, Math.max(1, ...data.observed.map((o) => o.n_validated))])
    .range([2, 9]);

  const path = (key: keyof CurvePoint) =>
    line<CurvePoint>()
      .defined((c) => c[key] !== null)
      .x((c) => x(c.confidence))
      .y((c) => y(c[key] as number))(data.curve) ?? "";

  const histPath =
    area<{ confidence: number; n: number }>()
      .curve(curveStepAfter)
      .x((h) => x(h.confidence))
      .y0(histTop + HIST_H)
      .y1((h) => histTop + HIST_H - histY(h.n))(hist) ?? "";

  const thresholdX = x(data.threshold);
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

          {/* Target and kept range */}
          <rect x={thresholdX} y={M.top} width={Math.max(0, M.left + plotW - thresholdX)} height={H} fill="rgba(78,205,196,0.05)" />
          <line x1={M.left} x2={M.left + plotW} y1={y(data.target)} y2={y(data.target)} stroke="#ff7a6b" strokeDasharray="4 4" opacity={0.7} />
          <text x={M.left + 4} y={y(data.target) - 5} className="fill-coral text-[10px]">
            {pct(data.target, 0)} target
          </text>

          {/* Observed share correct per confidence bin */}
          {data.observed.map((o) => (
            <circle
              key={o.confidence}
              cx={x(o.confidence)}
              cy={y(o.n_correct / o.n_validated)}
              r={radius(o.n_validated)}
              fill="rgba(255,255,255,0.18)"
              stroke="rgba(255,255,255,0.45)"
            >
              <title>
                {`${(o.confidence - 0.025).toFixed(2)}–${(o.confidence + 0.025).toFixed(2)}: ${o.n_correct} of ${o.n_validated} checked clips correct`}
              </title>
            </circle>
          ))}

          {/* Curves */}
          <path d={path("naive_precision_above")} fill="none" stroke="rgba(255,255,255,0.35)" strokeDasharray="2 3" strokeWidth={1.2} />
          {data.method === "logistic" && <path d={path("p_correct")} fill="none" stroke="#f4b860" strokeWidth={1.6} />}
          <path d={path("precision_above")} fill="none" stroke="#4ecdc4" strokeWidth={2.6} />

          {/* Threshold */}
          <line x1={thresholdX} x2={thresholdX} y1={M.top} y2={histTop + HIST_H} stroke="#4ecdc4" strokeWidth={1.5} />
          <text x={thresholdX + 5} y={M.top + 10} className="fill-teal text-[11px] font-medium">
            threshold {data.threshold.toFixed(2)}
          </text>

          {/* Distribution of all detections */}
          <path d={histPath} fill="rgba(127,184,255,0.35)" />
          <text x={M.left} y={histTop - 4} className="fill-white/40 text-[10px]">
            All BirdNET detections by confidence
          </text>

          {hover && (
            <line x1={x(hover.confidence)} x2={x(hover.confidence)} y1={M.top} y2={histTop + HIST_H} stroke="rgba(255,255,255,0.4)" />
          )}
        </svg>
      )}
      {hover && (
        <div
          className="pointer-events-none absolute z-10 w-56 rounded-lg border border-white/10 bg-ocean-950/95 p-3 text-xs shadow-xl"
          style={{ left: Math.min(x(hover.confidence) + 12, width - 232), top: M.top + 20 }}
        >
          <p className="font-medium">Keeping detections ≥ {hover.confidence.toFixed(2)}</p>
          <p className="mt-1 text-teal">{pct(hover.precision_above, 0)} of them correct</p>
          {hover.p_correct !== null && data.method === "logistic" && (
            <p className="text-amber">{pct(hover.p_correct, 0)} chance a detection at {hover.confidence.toFixed(2)} is correct</p>
          )}
          <p className="mt-1 text-white/50">
            {compact(hover.n_detections_above)} detections kept · {int(hover.n_validated_above)} checked clips above
          </p>
        </div>
      )}
    </div>
  );
}

function Explanation({ data }: { data: Calibration }) {
  const total = data.curve[0]?.n_detections_above ?? 0;
  const kept = data.curve.find((c) => Math.abs(c.confidence - data.threshold) < 0.001)?.n_detections_above;
  return (
    <div className="space-y-3 text-sm text-white/65">
      <p>
        <span className="text-white">{int(data.n_validated)} clips</span> were checked, spread evenly across BirdNET&rsquo;s
        confidence scores. Dots show the share that were correct at each score (bigger dot, more checks).
      </p>
      {data.method === "logistic" ? (
        <p>
          A logistic curve fitted to these checks, pulled towards the dots where many clips were checked, gives the{" "}
          <span className="text-amber">chance that a single detection is correct</span>. Weighting it by the scores of
          all {compact(total)} detections gives the{" "}
          <span className="text-teal">share correct among everything kept above each threshold</span>.
        </p>
      ) : (
        <p>
          The <span className="text-teal">teal line</span> is the share of checked clips that were correct above each
          threshold (no reliable curve could be fitted for this species).
        </p>
      )}
      <p>
        {data.threshold_source === "calibrated" ? (
          <>
            The threshold is the lowest confidence where that reaches {pct(data.target, 0)}:{" "}
            <span className="text-white">{data.threshold.toFixed(2)}</span>, keeping {compact(kept)} detections at about{" "}
            {pct(data.precision_at_threshold, 0)} precision.
          </>
        ) : data.threshold_source === "calibrated_low" ? (
          <>
            {pct(data.target, 0)} is never reached, so the best available threshold is used:{" "}
            <span className="text-white">{data.threshold.toFixed(2)}</span> (about {pct(data.precision_at_threshold, 0)}{" "}
            precise). Treat patterns with some caution.
          </>
        ) : (
          <>Precision stays too low at every threshold, so this species is not shown in the charts.</>
        )}
      </p>
      <p className="text-xs text-white/40">
        The dotted line is the uncorrected share of checked clips above each threshold. It over-weights whichever scores
        were checked more often than they occur, which is why it is not used.
      </p>
    </div>
  );
}
