"use client";

import { Pause, Play, RotateCcw } from "lucide-react";
import { useEffect, useRef } from "react";
import { weekLabel } from "@/lib/format";

const WEEK_MS = 260;

export function TimeLapse({
  week,
  onWeek,
  playing,
  onPlaying,
  weekStarts,
}: {
  week: number | null;
  onWeek: (w: number | null) => void;
  playing: boolean;
  onPlaying: (p: boolean) => void;
  weekStarts: string[];
}) {
  const weekRef = useRef(week);
  weekRef.current = week;

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      const next = (weekRef.current ?? 0) + 1;
      if (next > 53) {
        onPlaying(false);
        return;
      }
      onWeek(next);
    }, WEEK_MS);
    return () => clearInterval(id);
  }, [playing, onWeek, onPlaying]);

  return (
    <div className="flex items-center gap-3 rounded-full border border-white/15 bg-ocean-950/60 py-1 pl-1 pr-4">
      <button
        aria-label={playing ? "Pause time-lapse" : "Play time-lapse"}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-amber text-ocean-950 hover:bg-amber/90"
        onClick={() => {
          if (!playing && (week === null || week >= 53)) onWeek(1);
          onPlaying(!playing);
        }}
      >
        {playing ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
      </button>
      <input
        type="range"
        min={1}
        max={53}
        value={week ?? 1}
        onChange={(e) => {
          onPlaying(false);
          onWeek(Number(e.target.value));
        }}
        className="w-36 accent-amber md:w-56"
        aria-label="Week of the year"
      />
      <span className="w-20 whitespace-nowrap text-xs tabular-nums text-amber">
        {week ? weekLabel(weekStarts, week) : "Time-lapse"}
      </span>
      {week !== null && (
        <button
          aria-label="Reset time-lapse"
          className="text-white/50 hover:text-white"
          onClick={() => {
            onPlaying(false);
            onWeek(null);
          }}
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}
