"use client";

import { ArrowDownRight, ArrowRight, ArrowUpRight, HelpCircle } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { fetcher, type SpeciesDetail, type Trend } from "@/lib/api";
import { COUNTRY_COLORS, compact, displayName, int, pct, slug } from "@/lib/format";

export function TrendBadge({ trend }: { trend: Trend }) {
  const map = {
    rising: ["Rising", ArrowUpRight, "text-teal bg-teal/10"],
    falling: ["Falling", ArrowDownRight, "text-coral bg-coral/10"],
    steady: ["Steady", ArrowRight, "text-white/80 bg-white/10"],
    uncertain: ["Uncertain", HelpCircle, "text-white/50 bg-white/5"],
  } as const;
  const [label, Icon, cls] = map[trend.label];
  const title =
    trend.label === "uncertain"
      ? trend.reason
      : `${trend.from_year} → ${trend.to_year}, ${trend.weeks_compared} comparable weeks (×${trend.ratio.toFixed(2)})`;
  return (
    <span title={title} className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${cls}`}>
      <Icon className="h-3.5 w-3.5" /> {label}
    </span>
  );
}

export function MacaulayMedia({ media }: { media: SpeciesDetail["media"] }) {
  if (!media?.ml_photo_asset) {
    return (
      <div className="flex aspect-[4/3] items-center justify-center rounded-xl bg-gradient-to-br from-ocean-700 to-ocean-950 text-xs text-white/30">
        Photo coming soon
      </div>
    );
  }
  return (
    <figure>
      <iframe
        src={`https://macaulaylibrary.org/asset/${media.ml_photo_asset}/embed`}
        className="aspect-[4/3] w-full rounded-xl border-0"
        loading="lazy"
        allowFullScreen
        title="Macaulay Library photo"
      />
      <figcaption className="mt-1 text-[10px] text-white/40">
        {media.photo_credit ? `© ${media.photo_credit} / ` : ""}
        <a
          className="hover:text-white"
          href={`https://macaulaylibrary.org/asset/${media.ml_photo_asset}`}
          target="_blank"
          rel="noreferrer"
        >
          Macaulay Library ML{media.ml_photo_asset}
        </a>
      </figcaption>
    </figure>
  );
}

export function SpeciesCard({ species, compactView = false }: { species: string; compactView?: boolean }) {
  const { data } = useSWR<SpeciesDetail>(`/api/public/species/${encodeURIComponent(species)}`, fetcher);
  if (!data) return <div className="card h-64 animate-pulse" />;

  const [lo, hi] = data.hour_share_range;
  const maxCountry = Math.max(1, ...data.by_country.map((c) => c.n));

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-serif text-2xl leading-tight">{displayName(data)}</h3>
          <p className="text-sm italic text-white/45">{data.species}</p>
        </div>
        <TrendBadge trend={data.trend} />
      </div>

      {!compactView && (
        <div className="mt-4">
          <MacaulayMedia media={data.media} />
        </div>
      )}

      <div className="mt-5">
        <p className="eyebrow">Heard in</p>
        <p className="mt-1 font-serif text-4xl tabular-nums">{pct(data.hour_share)}</p>
        <p className="text-xs text-white/50">of recorded hours at sites where it occurs</p>
        <div className="relative mt-3 h-1.5 rounded-full bg-white/10">
          <div
            className="absolute h-full rounded-full bg-teal/40"
            style={{ left: `${Math.min(100, lo * 100)}%`, width: `${Math.max(1, (hi - lo) * 100)}%` }}
          />
          <div
            className="absolute -top-0.5 h-2.5 w-0.5 rounded bg-teal"
            style={{ left: `${Math.min(100, data.hour_share * 100)}%` }}
          />
        </div>
        <p className="mt-1 text-[11px] text-white/40">
          Middle half of {data.n_sites_occupied} sites: {pct(lo)}–{pct(hi)}
        </p>
      </div>

      <div className="mt-5 space-y-1.5">
        {data.by_country.map((c) => (
          <div key={c.country} className="flex items-center gap-2 text-xs">
            <span className="w-20 text-white/60">{c.country}</span>
            <div className="h-1.5 flex-1 rounded-full bg-white/5">
              <div
                className="h-full rounded-full"
                style={{ width: `${(c.n / maxCountry) * 100}%`, background: COUNTRY_COLORS[c.country] ?? "#fff" }}
              />
            </div>
            <span className="w-14 text-right tabular-nums text-white/50">{compact(c.n)}</span>
          </div>
        ))}
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-white/10 pt-4 text-xs text-white/55">
        {data.threshold_source === "default" ? (
          <span title="No validations yet: a conservative confidence threshold is used">
            Not yet validated · threshold {data.threshold.toFixed(2)}
          </span>
        ) : (
          <span>
            ✓ {int(data.n_validated)} clips checked · {pct(data.precision_at_threshold, 0)} precise at threshold{" "}
            {data.threshold.toFixed(2)}
          </span>
        )}
        {compactView && (
          <Link href={`/species/${slug(data.species)}`} className="ml-auto text-teal hover:underline">
            Details →
          </Link>
        )}
      </div>
    </div>
  );
}
