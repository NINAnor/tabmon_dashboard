"use client";

import { scaleSequential, scaleSqrt } from "d3-scale";
import { interpolateViridis, interpolateYlGnBu } from "d3-scale-chromatic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Map, { Layer, Popup, Source, type MapLayerMouseEvent, type MapRef } from "react-map-gl/maplibre";
import type { Cluster, SpeciesPhenology } from "@/lib/api";
import { oceanRamp } from "@/lib/color";
import { compact, int, weekLabel } from "@/lib/format";
import { useSize } from "@/lib/useSize";

export const DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

type Props = {
  clusters: Cluster[];
  phenology?: SpeciesPhenology | null;
  selected?: string | null;
  onSelect?: (id: string) => void;
  height?: number | string;
  /** When set, size and colour circles by activity in this week (time-lapse). */
  week?: number | null;
  /** Time-lapse scaling: each cluster against its own peak, or one shared scale. */
  mode?: "shape" | "absolute";
  /** Larger circles for the expanded time-lapse view. */
  large?: boolean;
};

export function ClusterMap({
  clusters,
  phenology,
  selected,
  onSelect,
  height = 560,
  week,
  mode = "absolute",
  large = false,
}: Props) {
  const [hover, setHover] = useState<{ id: string; lng: number; lat: number } | null>(null);
  const mapRef = useRef<MapRef>(null);

  // Fit all clusters in view whenever the data or the map size changes.
  const fit = useCallback(() => {
    if (!clusters.length || !mapRef.current) return;
    const lons = clusters.map((c) => c.lon);
    const lats = clusters.map((c) => c.lat);
    mapRef.current.resize();
    mapRef.current.fitBounds(
      [
        [Math.min(...lons), Math.min(...lats)],
        [Math.max(...lons), Math.max(...lats)],
      ],
      { padding: large ? 50 : 25, duration: 0 },
    );
  }, [clusters, large]);
  // Refit when the container is resized (e.g. the time-lapse layout expanding).
  const [wrapRef, size] = useSize<HTMLDivElement>();
  useEffect(() => {
    if (!size.width) return;
    const id = setTimeout(fit, 60);
    return () => clearTimeout(id);
  }, [fit, size.width, size.height]);

  const byId = useMemo(() => Object.fromEntries(clusters.map((c) => [c.id, c])), [clusters]);
  const phen = useMemo(
    () => Object.fromEntries((phenology?.groups ?? []).map((g) => [g.id, g])),
    [phenology],
  );

  const geojson = useMemo(() => {
    const size = scaleSqrt().domain([0, Math.max(1, ...clusters.map((c) => c.hours))]).range([5, 26]);
    const richness = scaleSequential(interpolateYlGnBu).domain([0, Math.max(1, ...clusters.map((c) => c.n_species)) * 1.15]);
    const starts = (phenology?.groups ?? [])
      .filter((g) => !g.sparse && g.total > 0 && g.onset_week !== null)
      .map((g) => ((g.onset_week! - (phenology?.season_start_week ?? 1) + 53) % 53));
    const startColor = scaleSequential(interpolateViridis).domain([
      Math.min(...starts, 52),
      Math.max(...starts, 1),
    ]);
    if (phenology && week) {
      const maxRate = Math.max(
        1e-9,
        ...phenology.groups.filter((g) => !g.sparse).flatMap((g) => g.weeks.map((w) => (w.low_effort ? 0 : w.rate ?? 0))),
      );
      return {
        type: "FeatureCollection" as const,
        features: clusters.map((c) => {
          const w = phen[c.id]?.weeks[week - 1];
          const g = phen[c.id];
          const live = w && !w.low_effort && w.rate !== null;
          const scale = mode === "shape" ? Math.max(1e-9, g?.peak_rate ?? 0) : maxRate;
          // Clusters with few detections stay small and muted, so stray detections
          // don't look like a real season.
          const t = live ? Math.min(1, Math.sqrt((w!.rate ?? 0) / scale)) * (g?.sparse ? 0.3 : 1) : 0;
          return {
            type: "Feature" as const,
            geometry: { type: "Point" as const, coordinates: [c.lon, c.lat] },
            properties: {
              id: c.id,
              color: !w || w.low_effort ? "#26323c" : t > 0 ? (g?.sparse ? "#5b7380" : oceanRamp(0.25 + 0.75 * t)) : "#33414d",
              radius: (large ? 5 : 4) + (large ? 38 : 26) * t,
              selected: c.id === selected ? 1 : 0,
            },
          };
        }),
      };
    }
    return {
      type: "FeatureCollection" as const,
      features: clusters.map((c) => {
        const g = phen[c.id];
        const detected = g && !g.sparse && g.total > 0 && g.onset_week !== null;
        const color = phenology
          ? detected
            ? startColor((g.onset_week! - phenology.season_start_week + 53) % 53)
            : "#33414d"
          : richness(c.n_species);
        return {
          type: "Feature" as const,
          geometry: { type: "Point" as const, coordinates: [c.lon, c.lat] },
          properties: {
            id: c.id,
            color,
            radius: phenology ? (detected ? 6 + 18 * Math.sqrt(g.peak_rate / Math.max(1e-9, ...phenology.groups.map((x) => x.peak_rate))) : 5) : size(c.hours),
            selected: c.id === selected ? 1 : 0,
          },
        };
      }),
    };
  }, [clusters, phen, phenology, selected, week, mode, large]);

  const onClick = (e: MapLayerMouseEvent) => {
    const id = e.features?.[0]?.properties?.id;
    if (id) onSelect?.(id);
  };

  const hovered = hover ? byId[hover.id] : null;
  const hoveredPhen = hover ? phen[hover.id] : null;

  return (
    <div ref={wrapRef} className="relative overflow-hidden rounded-2xl border border-white/10" style={{ height }}>
      <Map
        ref={mapRef}
        onLoad={fit}
        initialViewState={{ longitude: 8, latitude: 55, zoom: 3.1 }}
        mapStyle={DARK_STYLE}
        maxZoom={8}
        minZoom={1}
        interactiveLayerIds={["clusters"]}
        onClick={onClick}
        onMouseMove={(e) => {
          const f = e.features?.[0];
          setHover(f ? { id: f.properties.id, lng: e.lngLat.lng, lat: e.lngLat.lat } : null);
        }}
        onMouseLeave={() => setHover(null)}
        cursor={hover ? "pointer" : "grab"}
        attributionControl={{ compact: true }}
      >
        <Source id="clusters" type="geojson" data={geojson}>
          <Layer
            id="clusters-glow"
            type="circle"
            paint={{
              "circle-radius": ["*", ["get", "radius"], 2.2],
              "circle-radius-transition": { duration: 220 },
              "circle-color": ["get", "color"],
              "circle-opacity": 0.18,
              "circle-blur": 1,
            }}
          />
          <Layer
            id="clusters"
            type="circle"
            paint={{
              "circle-radius": ["get", "radius"],
              "circle-radius-transition": { duration: 220 },
              "circle-color": ["get", "color"],
              "circle-opacity": 0.9,
              "circle-stroke-color": ["case", ["==", ["get", "selected"], 1], "#ffffff", "#07131c"],
              "circle-stroke-width": ["case", ["==", ["get", "selected"], 1], 2.5, 1],
            }}
          />
        </Source>
        {hovered && hover && (
          <Popup longitude={hovered.lon} latitude={hovered.lat} closeButton={false} offset={14} maxWidth="260px">
            <div className="text-xs">
              <div className="font-serif text-sm text-white">{hovered.label}</div>
              <div className="text-white/50">{hovered.country}</div>
              {phenology && hoveredPhen ? (
                hoveredPhen.total > 0 ? (
                  <div className="mt-1.5 space-y-0.5">
                    <div>
                      Starts: <b>{hoveredPhen.onset_week !== null ? weekLabel(phenology.week_starts, hoveredPhen.onset_week) : "–"}</b>
                    </div>
                    <div>
                      Peak: <b>{hoveredPhen.peak_week !== null ? weekLabel(phenology.week_starts, hoveredPhen.peak_week) : "–"}</b>
                    </div>
                    <div>
                      Falls silent: <b>{hoveredPhen.end_week !== null ? weekLabel(phenology.week_starts, hoveredPhen.end_week) : "–"}</b>
                    </div>
                    <div>{int(hoveredPhen.total)} detections</div>
                  </div>
                ) : (
                  <div className="mt-1.5 text-white/50">Not detected</div>
                )
              ) : (
                <div className="mt-1.5 space-y-0.5">
                  <div>{hovered.n_species} species · {compact(hovered.detections)} detections</div>
                  <div>{compact(hovered.hours)} hours recorded · {hovered.n_sites} sites</div>
                </div>
              )}
            </div>
          </Popup>
        )}
      </Map>
      <div className="pointer-events-none absolute left-3 top-3 rounded-lg bg-ocean-950/80 px-3 py-2 text-[11px] text-white/60">
        {phenology && week
          ? mode === "shape"
            ? "Size & colour: this week vs each cluster's own peak"
            : "Size & colour: detections per hour this week"
          : phenology
            ? "Colour: start of the vocal season (early → late) · Size: peak activity"
            : "Colour: species richness · Size: hours recorded"}
        <div className="text-white/35">Locations are generalised to ~10 km</div>
        {phenology && week && (
          <div className="mt-2 flex items-end gap-3">
            {[0.15, 0.5, 1].map((t) => {
              const r = (large ? 5 : 4) + (large ? 38 : 26) * Math.sqrt(t);
              return (
                <span key={t} className="flex flex-col items-center gap-1">
                  <span
                    className="rounded-full border border-white/20"
                    style={{ width: r * 2 * 0.6, height: r * 2 * 0.6, background: oceanRamp(0.25 + 0.75 * Math.sqrt(t)) }}
                  />
                  <span className="text-[10px] text-white/45">
                    {t === 1 ? "peak" : `${Math.round(t * 100)}%`}
                  </span>
                </span>
              );
            })}
            <span className="flex flex-col items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-[#26323c]" />
              <span className="text-[10px] text-white/45">no data</span>
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
