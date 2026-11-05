"use client";

import { scaleLinear } from "d3-scale";
import useSWR from "swr";
import { PageTitle, Stat } from "@/components/ops/ui";
import { fetcher, type Dataset } from "@/lib/api";
import { COUNTRY_COLORS, compact, int } from "@/lib/format";
import { useSize } from "@/lib/useSize";

function MonthlyHours({ rows }: { rows: Dataset["monthly_hours"] }) {
  const [ref, { width }] = useSize<HTMLDivElement>();
  const months = [...new Set(rows.map((r) => r.month))].sort();
  const countries = Object.keys(COUNTRY_COLORS);
  const totals = months.map((m) => rows.filter((r) => r.month === m).reduce((s, r) => s + r.hours, 0));
  const H = 260;
  const y = scaleLinear().domain([0, Math.max(1, ...totals)]).range([0, H - 30]);
  const bw = months.length ? (width - 40) / months.length : 0;

  return (
    <div ref={ref}>
      <svg width={width} height={H}>
        {months.map((m, i) => {
          let acc = 0;
          return (
            <g key={m} transform={`translate(${40 + i * bw},0)`}>
              {countries.map((c) => {
                const v = rows.find((r) => r.month === m && r.country === c)?.hours ?? 0;
                const h = y(v);
                acc += h;
                return <rect key={c} x={1} width={Math.max(1, bw - 3)} y={H - 20 - acc} height={h} rx={2} fill={COUNTRY_COLORS[c]} opacity={0.85}>
                  <title>{`${c} · ${m.slice(0, 7)}: ${int(v)} h`}</title>
                </rect>;
              })}
              {(i % 2 === 0 || bw > 40) && (
                <text x={bw / 2} y={H - 5} fontSize={10} textAnchor="middle" fill="rgba(255,255,255,0.45)">
                  {new Date(m).toLocaleDateString("en-GB", { month: "short", year: "2-digit" })}
                </text>
              )}
            </g>
          );
        })}
        {y.ticks(4).map((t) => (
          <text key={t} x={34} y={H - 20 - y(t) + 3} fontSize={10} textAnchor="end" fill="rgba(255,255,255,0.4)">
            {compact(t)}
          </text>
        ))}
      </svg>
      <div className="mt-2 flex gap-4 text-xs text-white/60">
        {countries.map((c) => (
          <span key={c} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: COUNTRY_COLORS[c] }} /> {c}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function DatasetPage() {
  const { data } = useSWR<Dataset>("/api/ops/dataset", fetcher);
  const totalBytes = data?.total.total_size_bytes ?? 0;
  const maxRec = Math.max(1, ...(data?.devices ?? []).map((d) => d.total_recordings));

  return (
    <>
      <PageTitle eyebrow="Dataset" title="How much we have recorded" />
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Audio files" value={compact(data?.total.total_recordings ?? null)} />
        <Stat label="Volume" value={`${(totalBytes / 1024 ** 4).toFixed(1)} TB`} />
        <Stat label="Hours" value={compact((data?.total.total_recordings ?? 0) * 5 / 60)} sub="at 5 min per file" />
        <Stat label="Devices" value={data?.devices.length ?? "–"} />
      </div>

      <div className="card mt-6 p-5">
        <p className="eyebrow mb-4">Hours recorded per month</p>
        {data ? <MonthlyHours rows={data.monthly_hours} /> : <div className="h-64 animate-pulse rounded-xl bg-white/5" />}
      </div>

      <div className="card mt-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-white/[0.03] text-left text-xs text-white/50">
            <tr>
              <th className="px-3 py-2 font-medium">Device</th>
              <th className="px-3 py-2 font-medium">Site</th>
              <th className="px-3 py-2 font-medium">Share of dataset</th>
              <th className="px-3 py-2 text-right font-medium">Files</th>
              <th className="px-3 py-2 text-right font-medium">Size</th>
              <th className="px-3 py-2 font-medium">Period</th>
            </tr>
          </thead>
          <tbody>
            {data?.devices.map((d) => (
              <tr key={d.device} className="border-t border-white/5">
                <td className="px-3 py-2 font-mono text-xs text-white/60">{d.device_id}</td>
                <td className="px-3 py-2">
                  <span style={{ color: COUNTRY_COLORS[d.country ?? ""] }}>{d.country ?? "–"}</span>{" "}
                  <span className="text-white/60">
                    {d.cluster} · {d.site}
                  </span>
                </td>
                <td className="w-1/4 px-3 py-2">
                  <div className="h-1.5 rounded-full bg-white/5">
                    <div className="h-full rounded-full bg-teal/70" style={{ width: `${(d.total_recordings / maxRec) * 100}%` }} />
                  </div>
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{int(d.total_recordings)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{d.total_size_gb.toFixed(0)} GB</td>
                <td className="px-3 py-2 text-xs text-white/50">
                  {d.earliest_recording?.slice(0, 10)} → {d.latest_recording?.slice(0, 10)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
