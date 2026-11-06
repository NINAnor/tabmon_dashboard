"use client";

import { ArrowDown, ArrowUp } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import useSWR from "swr";
import { DeviceMap } from "@/components/ops/DeviceMap";
import { PageTitle, Stat, StatusDot } from "@/components/ops/ui";
import { fetcher, type Device } from "@/lib/api";
import { COUNTRY_COLORS, int, relativeDays } from "@/lib/format";

type SortKey = "country" | "cluster" | "site" | "status" | "days_since_last" | "total_recordings";

export default function DevicesPage() {
  const { data: devices = [], isLoading } = useSWR<Device[]>("/api/ops/devices", fetcher, {
    refreshInterval: 5 * 60_000,
  });
  const [country, setCountry] = useState("");
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; asc: boolean }>({ key: "days_since_last", asc: false });

  const countries = [...new Set(devices.map((d) => d.country))].sort();
  const filtered = useMemo(() => {
    const needle = q.toLowerCase();
    return devices
      .filter((d) => (!country || d.country === country) && (!status || d.status === status))
      .filter((d) => !needle || [d.site, d.cluster, d.device_id, d.deployment_id].some((v) => v?.toLowerCase().includes(needle)))
      .sort((a, b) => {
        const av = a[sort.key] ?? -Infinity;
        const bv = b[sort.key] ?? -Infinity;
        const cmp = av < bv ? -1 : av > bv ? 1 : 0;
        return sort.asc ? cmp : -cmp;
      });
  }, [devices, country, status, q, sort]);

  const online = filtered.filter((d) => d.status === "Online").length;
  const byCountry = countries.map((c) => {
    const ds = devices.filter((d) => d.country === c);
    return { country: c, online: ds.filter((d) => d.status === "Online").length, total: ds.length };
  });

  const header = (key: SortKey, label: string, right = false) => (
    <th className={`cursor-pointer select-none px-3 py-2 font-medium ${right ? "text-right" : ""}`} onClick={() => setSort((s) => ({ key, asc: s.key === key ? !s.asc : true }))}>
      <span className="inline-flex items-center gap-1">
        {label}
        {sort.key === key && (sort.asc ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
      </span>
    </th>
  );

  return (
    <>
      <PageTitle eyebrow="Device health" title="Recorders in the field">
        A device is online when it has uploaded a file within the last 3 days. Exact coordinates are visible to the team only.
      </PageTitle>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Devices shown" value={filtered.length} sub={`${devices.length} in total`} />
        <Stat label="Online" value={online} tone="good" sub={filtered.length ? `${Math.round((online / filtered.length) * 100)}%` : undefined} />
        <Stat label="Offline" value={filtered.length - online} tone="bad" />
        <Stat label="Recordings" value={int(filtered.reduce((s, d) => s + (d.total_recordings ?? 0), 0))} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px]">
        <DeviceMap devices={filtered} />
        <div className="card p-5">
          <p className="eyebrow mb-4">Status by country</p>
          <div className="space-y-4">
            {byCountry.map((c) => (
              <button key={c.country} className="block w-full text-left" onClick={() => setCountry(country === c.country ? "" : c.country)}>
                <div className="mb-1 flex justify-between text-sm">
                  <span style={{ color: COUNTRY_COLORS[c.country] }}>{c.country}</span>
                  <span className="tabular-nums text-white/60">
                    {c.online}/{c.total}
                  </span>
                </div>
                <div className="flex h-2.5 overflow-hidden rounded-full bg-coral/60">
                  <div className="bg-teal" style={{ width: `${(c.online / Math.max(1, c.total)) * 100}%` }} />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card mt-6 overflow-hidden">
        <div className="flex flex-wrap gap-3 border-b border-white/10 p-4">
          <input className="input max-w-xs" placeholder="Search site, cluster, device…" value={q} onChange={(e) => setQ(e.target.value)} />
          <select className="input max-w-[180px]" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">All countries</option>
            {countries.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <select className="input max-w-[160px]" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Any status</option>
            <option>Online</option>
            <option>Offline</option>
          </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-white/[0.03] text-left text-xs text-white/50">
              <tr>
                {header("status", "Status")}
                {header("country", "Country")}
                {header("cluster", "Cluster")}
                {header("site", "Site")}
                <th className="px-3 py-2 font-medium">Device</th>
                {header("days_since_last", "Last file")}
                {header("total_recordings", "Recordings", true)}
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-white/40">
                    Loading…
                  </td>
                </tr>
              )}
              {filtered.map((d) => (
                <tr key={d.device + d.deployment_id} className="border-t border-white/5 hover:bg-white/[0.03]">
                  <td className="px-3 py-2">
                    <StatusDot status={d.status} />
                  </td>
                  <td className="px-3 py-2" style={{ color: COUNTRY_COLORS[d.country] }}>
                    {d.country}
                  </td>
                  <td className="px-3 py-2">{d.cluster}</td>
                  <td className="px-3 py-2">
                    {d.site_id ? (
                      <Link className="hover:text-teal" href={`/ops/sites/${d.site_id}`}>
                        {d.site}
                      </Link>
                    ) : (
                      d.site
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-white/60">{d.device_id}</td>
                  <td className="px-3 py-2 text-white/70" title={d.last_file ?? ""}>
                    {relativeDays(d.days_since_last)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">{int(d.total_recordings)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
