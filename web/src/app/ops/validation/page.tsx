"use client";

import useSWR from "swr";
import { PageTitle, Stat } from "@/components/ops/ui";
import { fetcher, type Validations } from "@/lib/api";
import { COUNTRY_COLORS, displayName, int, pct } from "@/lib/format";

const SOURCE_LABEL: Record<string, string> = {
  calibrated: "Calibrated (≥90% precise)",
  calibrated_low: "Calibrated (best available)",
  default: "Default threshold",
};

export default function ValidationPage() {
  const { data } = useSWR<Validations>("/api/ops/validations", fetcher);
  const total = data?.by_country.reduce((s, r) => s + r.n_validated, 0) ?? 0;
  const correct = data?.by_country.reduce((s, r) => s + r.n_correct, 0) ?? 0;
  const countries = [...new Set(data?.by_country.map((r) => r.country))];
  const maxSpecies = Math.max(1, ...(data?.by_species ?? []).map((s) => s.n_validated));

  return (
    <>
      <PageTitle eyebrow="Validation" title="How many detections have been checked">
        Expert and citizen validations drive the per-species confidence thresholds used in every chart.
      </PageTitle>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Validated clips" value={int(total)} />
        <Stat label="Confirmed" value={pct(total ? correct / total : null)} sub="across all confidence levels" />
        <Stat label="Expert" value={int(data?.by_country.filter((r) => r.source === "expert").reduce((s, r) => s + r.n_validated, 0))} />
        <Stat label="Citizen" value={int(data?.by_country.filter((r) => r.source === "citizen").reduce((s, r) => s + r.n_validated, 0))} />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-4">
        {countries.map((c) => {
          const rows = data!.by_country.filter((r) => r.country === c);
          return (
            <div key={c} className="card p-4">
              <p className="font-serif text-xl" style={{ color: COUNTRY_COLORS[c ?? ""] }}>
                {c ?? "Unknown"}
              </p>
              {rows.map((r) => (
                <p key={r.source} className="mt-1 text-sm text-white/65">
                  {r.source}: <b className="text-white">{int(r.n_validated)}</b> clips · {r.n_species} species
                </p>
              ))}
            </div>
          );
        })}
      </div>

      <div className="card mt-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-white/[0.03] text-left text-xs text-white/50">
            <tr>
              <th className="px-3 py-2 font-medium">Species</th>
              <th className="px-3 py-2 font-medium">Validated</th>
              <th className="px-3 py-2 text-right font-medium">Confirmed</th>
              <th className="px-3 py-2 text-right font-medium">Threshold</th>
              <th className="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.by_species.map((s) => (
              <tr key={s.species} className="border-t border-white/5">
                <td className="px-3 py-2">
                  {displayName(s)} <span className="text-xs italic text-white/40">{s.species}</span>
                </td>
                <td className="w-1/3 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                      <div className="flex h-full" style={{ width: `${(s.n_validated / maxSpecies) * 100}%` }}>
                        <div className="bg-teal" style={{ width: `${(s.n_correct / s.n_validated) * 100}%` }} />
                        <div className="flex-1 bg-coral/60" />
                      </div>
                    </div>
                    <span className="w-14 text-right text-xs tabular-nums text-white/60">{int(s.n_validated)}</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{pct(s.n_correct / s.n_validated, 0)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{s.threshold?.toFixed(2) ?? "–"}</td>
                <td className="px-3 py-2 text-xs text-white/60">
                  {s.threshold_source ? SOURCE_LABEL[s.threshold_source] ?? s.threshold_source : "Excluded (unreliable)"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
