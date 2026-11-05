"use client";

import { X } from "lucide-react";
import Link from "next/link";
import { use, useState } from "react";
import useSWR from "swr";
import { PageTitle, Stat } from "@/components/ops/ui";
import { PlaceExplorer } from "@/components/PlaceExplorer";
import { fetcher, type SiteDetail } from "@/lib/api";
import { compact } from "@/lib/format";

const fmtDate = (s: string | null) => (s ? new Date(s).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "–");

export default function SitePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, error } = useSWR<SiteDetail>(`/api/ops/sites/${id}`, fetcher);
  const [zoom, setZoom] = useState<string | null>(null);

  if (error) return <p className="text-coral">Site not found.</p>;
  if (!data) return <div className="h-96 animate-pulse rounded-2xl bg-white/5" />;

  return (
    <>
      <Link href="/ops/sites" className="text-sm text-teal hover:underline">
        ← All sites
      </Link>
      <div className="mt-4">
        <PageTitle eyebrow={`${data.country} · ${data.cluster}`} title={data.site}>
          {data.habitat} · {data.lat.toFixed(5)}, {data.lon.toFixed(5)}
        </PageTitle>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Status" value={data.active ? "Active" : "Inactive"} tone={data.active ? "good" : undefined} />
        <Stat label="Hours recorded" value={compact(data.effort.hours)} />
        <Stat label="First recording" value={<span className="text-xl">{fmtDate(data.effort.first)}</span>} />
        <Stat label="Last recording" value={<span className="text-xl">{fmtDate(data.effort.last)}</span>} />
      </div>

      <div className="card mt-6 overflow-x-auto">
        <p className="eyebrow p-4 pb-2">Deployments</p>
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-white/50">
            <tr>
              {["Deployment", "Device", "Period", "Microphone", "GPS accuracy", "Comments"].map((h) => (
                <th key={h} className="px-4 py-2 font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.deployments.map((d) => (
              <tr key={d.deployment_id} className="border-t border-white/5 align-top">
                <td className="px-4 py-2 font-mono text-xs">{d.deployment_id}</td>
                <td className="px-4 py-2 font-mono text-xs text-white/60">{d.device_id}</td>
                <td className="px-4 py-2 text-xs">
                  {fmtDate(d.begin_ts)} → {d.end_ts ? fmtDate(d.end_ts) : "ongoing"}
                </td>
                <td className="px-4 py-2 text-xs">
                  {d.mic_height_cm ? `${d.mic_height_cm} cm` : "–"} · {d.mic_direction ?? "–"}
                </td>
                <td className="px-4 py-2 text-xs">{d.coord_uncertainty_m ? `${d.coord_uncertainty_m} m` : "–"}</td>
                <td className="max-w-md px-4 py-2 text-xs text-white/60">{d.comments}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-6">
        <p className="eyebrow mb-3">Field photos</p>
        {data.photos.length === 0 ? (
          <p className="text-sm text-white/40">No photos for this site.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">
            {data.photos.map((p) => (
              <button key={p.photo_id} className="group relative overflow-hidden rounded-xl" onClick={() => setZoom(p.photo_id)}>
                <img
                  src={`/api/ops/photos/${p.photo_id}`}
                  alt={p.picture_type}
                  loading="lazy"
                  className="aspect-square w-full object-cover transition-transform group-hover:scale-105"
                />
                <span className="absolute bottom-1 left-1 rounded bg-ocean-950/80 px-1.5 py-0.5 text-[10px] uppercase tracking-wider">
                  {p.picture_type}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="mt-8">
        <PlaceExplorer level="site" id={id} title="Soundscape at this site" showClips={false} />
      </div>

      {zoom && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/85 p-6" onClick={() => setZoom(null)}>
          <button className="absolute right-6 top-6 text-white/70 hover:text-white" aria-label="Close">
            <X className="h-6 w-6" />
          </button>
          <img src={`/api/ops/photos/${zoom}`} alt="" className="max-h-full max-w-full rounded-xl" />
        </div>
      )}
    </>
  );
}
