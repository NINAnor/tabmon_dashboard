// maplibre-gl 6 loads its web worker from a URL that the bundler does not ship, so the
// prebuild/predev script copies the worker to public/ and maplibre is pointed at it here.
// Only loaded in the browser; maps never initialise during server rendering.
export const mapLib =
  typeof window === "undefined"
    ? undefined
    : import("maplibre-gl").then((m) => {
        m.setWorkerUrl("/maplibre-gl-worker.mjs");
        return m;
      });
