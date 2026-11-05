"use client";

import { Camera } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { PageTitle } from "@/components/ops/ui";
import { fetcher, type SiteRow } from "@/lib/api";
import { COUNTRY_COLORS } from "@/lib/format";

export default function SitesPage() {
  const { data = [] } = useSWR<SiteRow[]>("/api/ops/sites", fetcher);
  const [q, setQ] = useState("");
  const needle = q.toLowerCase();
  const rows = data.filter((s) => !needle || `${s.country} ${s.cluster} ${s.site} ${s.habitat}`.toLowerCase().includes(needle));
  const countries = [...new Set(rows.map((s) => s.country))];

  return (
    <>
      <PageTitle eyebrow="Sites" title="Deployment sites">
        Metadata, deployment history and field photos for every site.
      </PageTitle>
      <input className="input mb-6 max-w-sm" placeholder="Filter sites…" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="space-y-10">
        {countries.map((c) => {
          const clusters = [...new Set(rows.filter((s) => s.country === c).map((s) => s.cluster))];
          return (
            <section key={c}>
              <h2 className="mb-4 font-serif text-2xl" style={{ color: COUNTRY_COLORS[c] }}>
                {c}
              </h2>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {clusters.map((cl) => (
                  <div key={cl} className="card p-4">
                    <p className="eyebrow mb-3">{cl}</p>
                    <ul className="space-y-1">
                      {rows
                        .filter((s) => s.country === c && s.cluster === cl)
                        .map((s) => (
                          <li key={s.site_id}>
                            <Link
                              href={`/ops/sites/${s.site_id}`}
                              className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-white/5"
                            >
                              <span className="flex items-center gap-2">
                                <span className={`h-1.5 w-1.5 rounded-full ${s.active ? "bg-teal" : "bg-white/25"}`} />
                                {s.site}
                              </span>
                              <span className="flex items-center gap-3 text-xs text-white/40">
                                {s.habitat}
                                {s.n_photos > 0 && (
                                  <span className="flex items-center gap-1">
                                    <Camera className="h-3 w-3" /> {s.n_photos}
                                  </span>
                                )}
                              </span>
                            </Link>
                          </li>
                        ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </>
  );
}
