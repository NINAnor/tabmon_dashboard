"use client";

import { AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, Headphones, HelpCircle } from "lucide-react";
import { labLink, MIN_VALIDATIONS } from "@/lib/lab";
import { EcologyChips, HowToRead, IucnBadge } from "./Ecology";
import useSWR from "swr";
import { fetcher, type SpeciesDetail, type Trend } from "@/lib/api";
import { COUNTRY_COLORS, compact, displayName, int, pct } from "@/lib/format";

function TrendBadge({ trend }: { trend: Trend }) {
  const map = {
    rising: ["Rising", ArrowUpRight, "text-beagle-green bg-beagle-green/10"],
    falling: ["Falling", ArrowDownRight, "text-coral bg-coral/10"],
    steady: ["Steady", ArrowRight, "text-beagle-mint/80 bg-white/10"],
    uncertain: ["Uncertain", HelpCircle, "text-beagle-mint/50 bg-white/5"],
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

function SpeciesMedia({ data, compact }: { data: SpeciesDetail; compact: boolean }) {
  const media = data.media;
  const info = data.info;
  const aspect = compact ? "aspect-[16/9]" : "aspect-[4/3]";

  if (media?.ml_photo_asset) {
    return (
      <figure>
        <iframe
          src={`https://macaulaylibrary.org/asset/${media.ml_photo_asset}/embed`}
          className={`${aspect} w-full rounded-xl border-0`}
          loading="lazy"
          allowFullScreen
          title="Macaulay Library photo"
        />
        <figcaption className="mt-1 text-[12px] text-beagle-mint/40">
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
  if (info?.image_url) {
    return (
      <figure>
        <img
          src={info.image_url}
          alt={displayName(data)}
          loading="lazy"
          className={`${aspect} w-full rounded-xl object-cover`}
        />
        <figcaption className="mt-1 truncate text-[12px] text-beagle-mint/40">
          Photo:{" "}
          <a className="hover:text-white" href={info.image_page ?? undefined} target="_blank" rel="noreferrer">
            {info.image_artist ?? "Wikimedia Commons"}
          </a>
          {info.image_license && (
            <>
              {" · "}
              {info.image_license_url ? (
                <a className="hover:text-white" href={info.image_license_url} target="_blank" rel="noreferrer">
                  {info.image_license}
                </a>
              ) : (
                info.image_license
              )}
            </>
          )}
        </figcaption>
      </figure>
    );
  }
  return compact ? null : (
    <div className={`flex ${aspect} items-center justify-center rounded-xl bg-gradient-to-br from-ocean-700 to-ocean-950 text-xs text-beagle-mint/30`}>
      No photo available
    </div>
  );
}

function SpeciesDescription({ data, compact }: { data: SpeciesDetail; compact: boolean }) {
  const info = data.info;
  if (!info?.extract) return null;
  return (
    <div className="mt-4">
      <p className={`text-sm leading-relaxed text-beagle-mint/70 ${compact ? "line-clamp-4" : ""}`}>{info.extract}</p>
      <p className="mt-1 text-[12px] text-beagle-mint/40">
        From{" "}
        <a className="hover:text-white" href={info.wiki_url ?? undefined} target="_blank" rel="noreferrer">
          Wikipedia
        </a>{" "}
        ·{" "}
        <a className="hover:text-white" href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">
          CC BY-SA 4.0
        </a>
      </p>
    </div>
  );
}

export function useSpeciesDetail(species: string | null) {
  return useSWR<SpeciesDetail>(species ? `/api/public/species/${encodeURIComponent(species)}` : null, fetcher);
}

/** Photo, names, status badges, ecology chips and the Wikipedia description. */
export function SpeciesHeader({ species }: { species: string }) {
  const { data } = useSpeciesDetail(species);
  if (!data) return <div className="card h-72 animate-pulse" />;
  return (
    <div className="card grid gap-6 p-5 md:grid-cols-[minmax(0,380px)_1fr]">
      <SpeciesMedia data={data} compact={false} />
      <div>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-serif text-4xl leading-tight">{displayName(data)}</h2>
            <p className="italic text-beagle-mint/45">{data.species}</p>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <IucnBadge ecology={data.ecology} />
            <TrendBadge trend={data.trend} />
            {data.threshold_source === "default" && (
              <span
                className="inline-flex items-center gap-1 rounded-full border border-coral/40 bg-coral/10 px-2 py-0.5 text-[12px] text-coral"
                title="Too few expert/citizen checks to calibrate BirdNET for this species. Some detections may be false positives."
              >
                <AlertTriangle className="h-3 w-3" /> Not yet validated · treat with caution
              </span>
            )}
          </div>
        </div>
        <div className="mt-3">
          <EcologyChips ecology={data.ecology} />
        </div>
        <SpeciesDescription data={data} compact={false} />
      </div>
    </div>
  );
}

export function SpeciesHowToRead({ species }: { species: string }) {
  const { data } = useSpeciesDetail(species);
  return <HowToRead ecology={data?.ecology ?? null} />;
}

/** Key numbers: share of hours heard, detections per country, validation status. */
export function SpeciesStats({ species }: { species: string }) {
  const { data } = useSpeciesDetail(species);
  if (!data) return <div className="card h-40 animate-pulse" />;
  const [lo, hi] = data.hour_share_range;
  const maxCountry = Math.max(1, ...data.by_country.map((c) => c.n));

  return (
    <div className="grid gap-px overflow-hidden rounded-2xl border border-beagle-mint/10 bg-white/10 md:grid-cols-3">
      <div className="bg-ocean-900 p-5">
        <p className="eyebrow">Heard in</p>
        <p className="mt-1 font-serif text-4xl tabular-nums">{pct(data.hour_share)}</p>
        <p className="text-xs text-beagle-mint/50">of recorded hours at the {data.n_sites_occupied} sites where it occurs</p>
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
        <p className="mt-1 text-[12px] text-beagle-mint/40">
          Middle half of sites: {pct(lo)}–{pct(hi)}
        </p>
      </div>

      <div className="bg-ocean-900 p-5">
        <p className="eyebrow mb-3">Detections by country</p>
        <div className="space-y-1.5">
          {data.by_country.map((c) => (
            <div key={c.country} className="flex items-center gap-2 text-xs">
              <span className="w-20 text-beagle-mint/60">{c.country}</span>
              <div className="h-1.5 flex-1 rounded-full bg-white/5">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${(c.n / maxCountry) * 100}%`, background: COUNTRY_COLORS[c.country] ?? "#fff" }}
                />
              </div>
              <span className="w-14 text-right tabular-nums text-beagle-mint/50">{compact(c.n)}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-ocean-900 p-5">
        <p className="eyebrow">Validation</p>
        {data.threshold_source === "default" ? (
          <>
            <p className="mt-1 font-serif text-2xl">
              {data.n_validated > 0 ? `${int(data.n_validated)} clips checked` : "Not yet validated"}
            </p>
            <div className="mt-2 h-1.5 rounded-full bg-white/10">
              <div
                className="h-full rounded-full bg-amber"
                style={{ width: `${Math.min(100, (data.n_validated / MIN_VALIDATIONS) * 100)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-beagle-mint/50">
              {Math.max(0, MIN_VALIDATIONS - data.n_validated)} more checks needed to calibrate. Until then a
              conservative confidence threshold of {data.threshold.toFixed(2)} is used, so treat patterns with caution.
            </p>
          </>
        ) : (
          <>
            <p className="mt-1 font-serif text-2xl">
              ≥ {data.threshold_source === "calibrated_low" ? "70" : "90"}%{" "}
              <span className="text-base text-beagle-mint/60">chance correct</span>
            </p>
            <p className="mt-1 text-xs text-beagle-mint/50">
              {int(data.n_validated)} clips checked by experts and citizens. Only detections from BirdNET confidence{" "}
              {data.threshold.toFixed(2)}
              {data.threshold_lower != null && data.threshold_upper != null
                ? ` (${data.threshold_lower.toFixed(2)}–${data.threshold_upper.toFixed(2)})`
                : ""}{" "}
              are counted, where each has at least that chance of being right
              {data.threshold_source === "calibrated_low" ? " (the 90% target is never reached)" : ""}.{" "}
              {data.threshold_method && (
                <a href="#calibration" className="text-teal hover:underline">
                  How this was set ↓
                </a>
              )}
            </p>
          </>
        )}
        <a
          href={labLink({ country: data.by_country[0]?.country, species: data.species })}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-beagle-green/15 px-3 py-1.5 text-xs font-medium text-beagle-green hover:bg-beagle-green/25"
        >
          <Headphones className="h-3.5 w-3.5" />
          {data.threshold_source === "default" ? `Help validate the ${displayName(data)}` : "Check more clips"} →
        </a>
      </div>
    </div>
  );
}
