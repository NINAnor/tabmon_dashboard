// Small colour helpers shared by the heatmap-style charts.

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function makeRamp(stops: string[]) {
  const rgb = stops.map(hexToRgb);
  return (t: number) => {
    const c = Math.min(1, Math.max(0, t)) * (rgb.length - 1);
    const i = Math.min(rgb.length - 2, Math.floor(c));
    const f = c - i;
    const [a, b] = [rgb[i], rgb[i + 1]];
    const mix = a.map((v, k) => Math.round(v + (b[k] - v) * f));
    return `rgb(${mix[0]},${mix[1]},${mix[2]})`;
  };
}

/** Deep ocean → teal → pale gold. */
export const oceanRamp = makeRamp(["#0f2433", "#145a66", "#2fa59c", "#8be0c9", "#f6e7a8"]);

/** 256-entry [r, g, b, a] colour map (0–1) for the wavesurfer spectrogram. */
export function spectrogramColorMap(): number[][] {
  const stops = ["#07131c", "#0f2433", "#145a66", "#2fa59c", "#8be0c9", "#f6e7a8", "#ffffff"].map(hexToRgb);
  return Array.from({ length: 256 }, (_, i) => {
    const c = (i / 255) * (stops.length - 1);
    const k = Math.min(stops.length - 2, Math.floor(c));
    const f = c - k;
    const [a, b] = [stops[k], stops[k + 1]];
    return [...a.map((v, j) => (v + (b[j] - v) * f) / 255), 1];
  });
}
