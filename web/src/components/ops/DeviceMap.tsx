"use client";

import { useMemo, useState } from "react";
import Map, { Layer, Popup, Source } from "react-map-gl/maplibre";
import type { Device } from "@/lib/api";
import { int, relativeDays } from "@/lib/format";
import { DARK_STYLE } from "../ClusterMap";

export function DeviceMap({ devices, height = 520 }: { devices: Device[]; height?: number }) {
  const [hover, setHover] = useState<Device | null>(null);
  const byDevice = useMemo(() => Object.fromEntries(devices.map((d) => [d.device + d.deployment_id, d])), [devices]);

  const geojson = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: devices
        .filter((d) => d.lat !== null && d.lon !== null)
        .map((d) => ({
          type: "Feature" as const,
          geometry: { type: "Point" as const, coordinates: [d.lon, d.lat] },
          properties: { key: d.device + d.deployment_id, online: d.status === "Online" ? 1 : 0 },
        })),
    }),
    [devices],
  );

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10" style={{ height }}>
      <Map
        initialViewState={{ longitude: 8, latitude: 55, zoom: 3.2 }}
        mapStyle={DARK_STYLE}
        interactiveLayerIds={["devices"]}
        onMouseMove={(e) => setHover(byDevice[e.features?.[0]?.properties?.key] ?? null)}
        onMouseLeave={() => setHover(null)}
        cursor={hover ? "pointer" : "grab"}
      >
        <Source id="devices" type="geojson" data={geojson}>
          <Layer
            id="devices-glow"
            type="circle"
            paint={{
              "circle-radius": 14,
              "circle-color": ["case", ["==", ["get", "online"], 1], "#4ecdc4", "#ff7a6b"],
              "circle-opacity": 0.15,
              "circle-blur": 1,
            }}
          />
          <Layer
            id="devices"
            type="circle"
            paint={{
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 4, 10, 8],
              "circle-color": ["case", ["==", ["get", "online"], 1], "#4ecdc4", "#ff7a6b"],
              "circle-stroke-color": "#07131c",
              "circle-stroke-width": 1.5,
            }}
          />
        </Source>
        {hover && (
          <Popup longitude={hover.lon} latitude={hover.lat} closeButton={false} offset={12}>
            <div className="space-y-0.5 text-xs">
              <div className="font-serif text-sm text-white">
                {hover.cluster} · {hover.site}
              </div>
              <div className="text-white/50">{hover.deployment_id}</div>
              <div className={hover.status === "Online" ? "text-teal" : "text-coral"}>
                {hover.status} · last file {relativeDays(hover.days_since_last)}
              </div>
              <div>{int(hover.total_recordings)} recordings</div>
              <div className="text-white/40">
                {hover.lat.toFixed(5)}, {hover.lon.toFixed(5)}
              </div>
            </div>
          </Popup>
        )}
      </Map>
    </div>
  );
}
