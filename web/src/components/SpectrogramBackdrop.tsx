"use client";

import { useEffect, useRef } from "react";

/**
 * Decorative scrolling "spectrogram": synthetic chirps drifting right to left,
 * evoking the dawn chorus without using any real (private) recordings.
 */
export function SpectrogramBackdrop() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let width = 0;
    let height = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const resize = () => {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    type Chirp = { x: number; f: number; kind: number; size: number; hue: number; a: number };
    const chirps: Chirp[] = [];
    const spawn = (x: number) => {
      chirps.push({
        x,
        f: 0.2 + Math.random() * 0.65,
        kind: Math.floor(Math.random() * 4),
        size: 0.6 + Math.random() * 1.2,
        hue: Math.random() < 0.75 ? 174 : 38,
        a: 0.25 + Math.random() * 0.5,
      });
    };
    for (let x = 0; x < 1.2; x += 0.012) if (Math.random() < 0.5) spawn(x);

    const draw = (c: Chirp) => {
      const x0 = c.x * width;
      const y0 = (1 - c.f) * height;
      const s = c.size * Math.min(width, 1400) * 0.02;
      ctx.strokeStyle = `hsla(${c.hue}, 65%, 62%, ${c.a})`;
      ctx.lineWidth = 1.5 + c.size;
      ctx.lineCap = "round";
      ctx.beginPath();
      if (c.kind === 0) {
        // Downsweep
        ctx.moveTo(x0, y0 - s);
        ctx.quadraticCurveTo(x0 + s * 0.3, y0, x0 + s * 0.9, y0 + s * 0.8);
      } else if (c.kind === 1) {
        // Trill
        for (let i = 0; i < 5; i++) {
          const xi = x0 + i * s * 0.35;
          ctx.moveTo(xi, y0 - s * 0.4);
          ctx.lineTo(xi + s * 0.12, y0 + s * 0.4);
        }
      } else if (c.kind === 2) {
        // Whistle
        ctx.moveTo(x0, y0);
        ctx.bezierCurveTo(x0 + s * 0.6, y0 - s * 0.5, x0 + s * 1.2, y0 + s * 0.5, x0 + s * 1.8, y0);
      } else {
        // Upsweep
        ctx.moveTo(x0, y0 + s * 0.6);
        ctx.quadraticCurveTo(x0 + s * 0.5, y0 + s * 0.4, x0 + s * 0.8, y0 - s * 0.8);
      }
      ctx.stroke();
    };

    let raf = 0;
    let last = performance.now();
    const frame = (now: number) => {
      const dt = Math.min(64, now - last) / 1000;
      last = now;
      ctx.clearRect(0, 0, width, height);
      for (const c of chirps) {
        c.x -= dt * 0.025;
        draw(c);
      }
      while (chirps.length && chirps[0].x < -0.1) chirps.shift();
      if (Math.random() < dt * 22) spawn(1.05 + Math.random() * 0.1);
      chirps.sort((a, b) => a.x - b.x);
      raf = requestAnimationFrame(frame);
    };
    if (reduced) {
      for (const c of chirps) draw(c);
    } else {
      raf = requestAnimationFrame(frame);
    }
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={ref} className="absolute inset-0 h-full w-full opacity-60" aria-hidden />;
}
