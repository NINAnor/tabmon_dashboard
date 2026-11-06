"use client";

import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import { PageTitle, Stat } from "@/components/ops/ui";
import { fetcher, type Activity } from "@/lib/api";
import { oceanRamp } from "@/lib/color";
import { COUNTRY_COLORS, int } from "@/lib/format";
import { useSize } from "@/lib/useSize";

const LABEL_W = 230;
const ROW = 11;
const TOP = 24;
const FULL_DAY = 288; // 5-minute files per day

export default function ActivityPage() {
  const { data } = useSWR<Activity>("/api/ops/activity", fetcher);
  const [days, setDays] = useState(180);
  const [ref, { width }] = useSize<HTMLDivElement>();
  const canvas = useRef<HTMLCanvasElement>(null);
  const [hover, setHover] = useState<{ r: number; c: number; x: number; y: number } | null>(null);

  const dates = data ? data.dates.slice(-days) : [];
  const offset = data ? data.dates.length - dates.length : 0;
  const rows = data?.rows ?? [];
  const height = TOP + rows.length * ROW + 10;
  const plotW = Math.max(100, width - LABEL_W - 8);
  const cw = dates.length ? plotW / dates.length : 1;

  useEffect(() => {
    const el = canvas.current;
    if (!el || !data || width === 0) return;
    const dpr = window.devicePixelRatio || 1;
    el.width = width * dpr;
    el.height = height * dpr;
    const ctx = el.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.font = "10px var(--font-inter), sans-serif";

    // Month labels
    ctx.fillStyle = "rgba(255,255,255,0.45)";
    dates.forEach((d, i) => {
      if (d.endsWith("-01")) {
        const x = LABEL_W + i * cw;
        ctx.fillText(new Date(d).toLocaleDateString("en-GB", { month: "short", year: "2-digit" }), x + 2, 14);
        ctx.fillRect(x, TOP - 4, 1, rows.length * ROW + 4);
      }
    });

    let prevCountry = "";
    rows.forEach((r, ri) => {
      const y = TOP + ri * ROW;
      if (r.country !== prevCountry) {
        ctx.fillStyle = "rgba(255,255,255,0.15)";
        if (ri > 0) ctx.fillRect(0, y - 1, width, 1);
        prevCountry = r.country;
      }
      ctx.fillStyle = COUNTRY_COLORS[r.country] ?? "#fff";
      ctx.fillRect(4, y + 2, 3, ROW - 4);
      ctx.fillStyle = "rgba(255,255,255,0.75)";
      const label = `${r.cluster ?? ""} · ${r.site ?? r.device_id}`;
      ctx.fillText(label.length > 36 ? `${label.slice(0, 35)}…` : label, 12, y + ROW - 2);
      for (let i = 0; i < dates.length; i++) {
        const v = r.values[offset + i];
        ctx.fillStyle = v ? oceanRamp(Math.min(1, v / FULL_DAY)) : "#0b1822";
        ctx.fillRect(LABEL_W + i * cw, y, Math.max(1, cw - (cw > 3 ? 1 : 0)), ROW - 1);
      }
    });
  }, [data, width, height, days, cw, dates, offset, rows]);

  const total = rows.reduce((s, r) => s + r.values.slice(-days).reduce((a, b) => a + b, 0), 0);
  const expected = rows.length * dates.length * FULL_DAY;

  return (
    <>
      <PageTitle eyebrow="Recording activity" title="Files uploaded per device per day">
        A full day is {FULL_DAY} five-minute files. Gaps show power, SIM or hardware issues.
      </PageTitle>
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Devices" value={rows.length} />
        <Stat label="Files in window" value={int(total)} />
        <Stat label="Uptime in window" value={expected ? `${Math.round((total / expected) * 100)}%` : "–"} />
        <div className="card flex items-center gap-2 px-5 py-4">
          {[30, 90, 180, 365, 10_000].map((d) => (
            <button key={d} className={`pill ${days === d ? "pill-active" : ""}`} onClick={() => setDays(d)}>
              {d >= 10_000 ? "All" : `${d}d`}
            </button>
          ))}
        </div>
      </div>
      <div ref={ref} className="card relative overflow-hidden p-3">
        {!data && <div className="h-[600px] animate-pulse rounded-xl bg-white/5" />}
        <canvas
          ref={canvas}
          style={{ width, height }}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const r = Math.floor((y - TOP) / ROW);
            const c = Math.floor((x - LABEL_W) / cw);
            if (r < 0 || r >= rows.length || c < 0 || c >= dates.length) return setHover(null);
            setHover({ r, c, x, y });
          }}
          onMouseLeave={() => setHover(null)}
        />
        {hover && (
          <div className="tooltip" style={{ left: Math.min(hover.x + 14, width - 220), top: hover.y + 14 }}>
            <div className="font-medium text-white">
              {rows[hover.r].cluster} · {rows[hover.r].site}
            </div>
            <div className="font-mono text-white/45">{rows[hover.r].device_id}</div>
            <div className="mt-1">
              {dates[hover.c]}: <span className="text-teal">{rows[hover.r].values[offset + hover.c]}</span> files
            </div>
          </div>
        )}
      </div>
    </>
  );
}
