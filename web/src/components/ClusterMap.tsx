"use client";

import { scaleSequential, scaleSqrt } from "d3-scale";
import { interpolateViridis, interpolateYlGnBu } from "d3-scale-chromatic";
import { useMemo, useState } from "react";
import Map, { Layer, Popup, Source, type MapLayerMouseEvent } from "react-map-gl/maplibre";
import type { Cluster, SpeciesPhenology } from "@/lib/api";
import { compact, int, weekLabel } from "@/lib/format";

export const DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

type Props = {
  clusters: Cluster[];
  phenology?: SpeciesPhenology | null;
  selected?: string | null;
  onSelect?: (id: string) => void;
  height?: number | string;
};

export function ClusterMap({ clusters, phenology, selected, onSelect, height = 560 }: Props) {
  const [hover, setHover] = useState<{ id: string; lng: number; lat: number } | null>(null);

  const byId = useMemo(() => Object.fromEntries(clusters.map((c) => [c.id, c])), [clusters]);
  const phen = useMemo(
    () => Object.fromEntries((phenology?.groups ?? []).map((g) => [g.id, g])),
    [phenology],
  );

  const geojson = useMemo(() => {
    const size = scaleSqrt().domain([0, Math.max(1, ...clusters.map((c) => c.hours))]).range([5, 26]);
    const richness = scaleSequential(interpolateYlGnBu).domain([0, Math.max(1, ...clusters.map((c) => c.n_species)) * 1.15]);
    const medians = (phenology?.groups ?? []).filter((g) => !g.sparse).map((g) => g.median_week).filter((w): w is number => w !== null);
    const arrival = scaleSequential(interpolateViridis).domain([
      Math.min(...medians, 52),
      Math.max(...medians, 1),
    ]);
    return {
      type: "FeatureCollection" as const,
      features: clusters.map((c) => {
        const g = phen[c.id];
        const detected = g && !g.sparse && g.total > 0 && g.median_week;
        const color = phenology
          ? detected
            ? arrival(g.median_week!)
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
  }, [clusters, phen, phenology, selected]);

  const onClick = (e: MapLayerMouseEvent) => {
    const id = e.features?.[0]?.properties?.id;
    if (id) onSelect?.(id);
  };

  const hovered = hover ? byId[hover.id] : null;
  const hoveredPhen = hover ? phen[hover.id] : null;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10" style={{ height }}>
      <Map
        initialViewState={{ longitude: 8, latitude: 55, zoom: 3.1 }}
        mapStyle={DARK_STYLE}
        maxZoom={8}
        minZoom={2.5}
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
                      Arrival: <b>{hoveredPhen.first_week ? weekLabel(phenology.week_starts, hoveredPhen.first_week) : "–"}</b>
                    </div>
                    <div>
                      Mid-season: <b>{hoveredPhen.median_week ? weekLabel(phenology.week_starts, hoveredPhen.median_week) : "–"}</b>
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
        {phenology ? "Colour: mid-season date (early → late) · Size: peak activity" : "Colour: species richness · Size: hours recorded"}
        <div className="text-white/35">Locations are generalised to ~10 km</div>
      </div>
    </div>
  );
}
