"use client";

import useSWR from "swr";
import { PageTitle, Stat } from "@/components/ops/ui";
import { fetcher, type Validations } from "@/lib/api";
import { COUNTRY_COLORS, displayName, int, pct } from "@/lib/format";

const SOURCE_LABEL: Record<string, string> = {
  calibrated: "Calibrated (≥90% chance correct)",
  calibrated_low: "Calibrated (≥70% only)",
  default: "Default threshold",
};

export default function ValidationPage() {
  const { data } = useSWR<Validations>("/api/ops/validations", fetcher);
  const total = data?.by_country.reduce((s, r) => s + r.n_validated, 0) ?? 0;
  const correct = data?.by_country.reduce((s, r) => s + r.n_correct, 0) ?? 0;
  const clips = (source?: string) =>
    data?.by_country.filter((r) => !source || r.source === source).reduce((s, r) => s + (r.n_clips ?? 0), 0);
  const countries = [...new Set(data?.by_country.map((r) => r.country))];
  const maxSpecies = Math.max(1, ...(data?.by_species ?? []).map((s) => s.n_validated));

  return (
    <>
      <PageTitle eyebrow="Validation" title="How many detections have been checked">
        Expert and citizen validations drive the per-species confidence thresholds used in every chart.
      </PageTitle>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Stat label="Clips checked" value={int(clips())} sub={`${int(clips("expert"))} expert · ${int(clips("citizen"))} citizen`} />
        <Stat label="Detections checked" value={int(total)} sub="one per BirdNET species in a clip" />
        <Stat label="Confirmed" value={pct(total ? correct / total : null)} sub="of detections, all confidence levels" />
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
                <p key={r.source} className="mt-1 text-sm text-beagle-mint/65">
                  {r.source}: {r.n_clips != null && <><b className="text-white">{int(r.n_clips)}</b> clips · </>}
                  {int(r.n_validated)} detections · {r.n_species} species
                </p>
              ))}
            </div>
          );
        })}
      </div>

      <div className="card mt-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-white/[0.03] text-left text-xs text-beagle-mint/50">
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
              <tr key={s.species} className="border-t border-beagle-mint/5">
                <td className="px-3 py-2">
                  {displayName(s)} <span className="text-xs italic text-beagle-mint/40">{s.species}</span>
                </td>
                <td className="w-1/3 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                      <div className="flex h-full" style={{ width: `${(s.n_validated / maxSpecies) * 100}%` }}>
                        <div className="bg-beagle-green" style={{ width: `${(s.n_correct / s.n_validated) * 100}%` }} />
                        <div className="flex-1 bg-coral/60" />
                      </div>
                    </div>
                    <span className="w-14 text-right text-xs tabular-nums text-beagle-mint/60">{int(s.n_validated)}</span>
                  </div>
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{pct(s.n_correct / s.n_validated, 0)}</td>
                <td className="px-3 py-2 text-right tabular-nums">{s.threshold?.toFixed(2) ?? "–"}</td>
                <td className="px-3 py-2 text-xs text-beagle-mint/60">
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
