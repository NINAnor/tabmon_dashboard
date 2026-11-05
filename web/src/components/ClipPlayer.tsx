"use client";

import { CheckCircle2, Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import useSWR from "swr";
import WaveSurfer from "wavesurfer.js";
import Spectrogram from "wavesurfer.js/dist/plugins/spectrogram.esm.js";
import { fetcher, qs, type Clip } from "@/lib/api";
import { spectrogramColorMap } from "@/lib/color";
import { displayName } from "@/lib/format";

const COLOR_MAP = typeof window !== "undefined" ? spectrogramColorMap() : [];

export function ClipList({
  species,
  clusterId,
  month,
  limit = 6,
  title = "Listen",
}: {
  species?: string | null;
  clusterId?: string | null;
  month?: number | null;
  limit?: number;
  title?: string;
}) {
  const { data, isLoading } = useSWR<Clip[]>(
    `/api/public/clips${qs({ species, cluster_id: clusterId, month, limit })}`,
    fetcher,
  );
  const [active, setActive] = useState<string | null>(null);

  return (
    <div>
      <p className="eyebrow mb-3">{title}</p>
      {isLoading && <p className="text-sm text-white/40">Loading recordings…</p>}
      {data && data.length === 0 && (
        <p className="text-sm text-white/40">No example recordings for this selection yet.</p>
      )}
      <ul className="space-y-2">
        {data?.map((c) => (
          <li key={c.clip_id}>
            <ClipRow clip={c} active={active === c.clip_id} onPlay={() => setActive(c.clip_id)} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function ClipRow({ clip, active, onPlay }: { clip: Clip; active: boolean; onPlay: () => void }) {
  const wave = useRef<HTMLDivElement>(null);
  const spec = useRef<HTMLDivElement>(null);
  const ws = useRef<WaveSurfer | null>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (!active || !wave.current || !spec.current) return;
    setLoading(true);
    setError(false);
    const w = WaveSurfer.create({
      container: wave.current,
      url: `/api/clips/${clip.clip_id}.mp3`,
      height: 28,
      waveColor: "rgba(78,205,196,0.35)",
      progressColor: "#4ecdc4",
      cursorColor: "#f4b860",
      cursorWidth: 1,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      sampleRate: 22050,
      plugins: [
        Spectrogram.create({
          container: spec.current,
          height: 110,
          labels: true,
          labelsBackground: "rgba(5,13,20,0.55)",
          labelsColor: "rgba(255,255,255,0.6)",
          labelsHzColor: "rgba(255,255,255,0.6)",
          frequencyMax: 11000,
          fftSamples: 512,
          colorMap: COLOR_MAP,
        }),
      ],
    });
    w.on("ready", (d) => {
      setLoading(false);
      setDuration(d);
      w.play();
    });
    w.on("play", () => setPlaying(true));
    w.on("pause", () => setPlaying(false));
    w.on("finish", () => setPlaying(false));
    w.on("error", () => {
      setLoading(false);
      setError(true);
    });
    ws.current = w;
    return () => {
      w.destroy();
      ws.current = null;
      setPlaying(false);
      setDuration(0);
    };
  }, [active, clip.clip_id]);

  const meta = (
    <>
      <p className="truncate text-sm">{displayName(clip)}</p>
      <p className="truncate text-xs text-white/45">
        {clip.cluster ?? clip.cluster_id} · {clip.country} ·{" "}
        {new Date(clip.recorded_on).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
      </p>
    </>
  );

  return (
    <div className={`card px-3 py-2 ${active ? "border-teal/40" : ""}`}>
      <div className="flex items-center gap-3">
        <button
          aria-label={playing ? "Pause" : "Play"}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal/15 text-teal hover:bg-teal/25"
          onClick={() => (active && ws.current ? ws.current.playPause() : onPlay())}
        >
          {playing ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
        </button>
        <div className="min-w-0 flex-1">{meta}</div>
        {clip.validated ? (
          <span title="Checked by a validator" className="flex items-center gap-1 text-[11px] text-teal">
            <CheckCircle2 className="h-3.5 w-3.5" /> checked
          </span>
        ) : (
          <span title="BirdNET confidence" className="text-[11px] tabular-nums text-white/40">
            {Math.round(clip.confidence * 100)}%
          </span>
        )}
      </div>

      {active && (
        <div className="mt-3">
          {loading && <p className="mb-1 text-xs text-white/45">Fetching recording…</p>}
          {error && <p className="text-xs text-coral">Recording unavailable</p>}
          <div className={`relative ${error ? "hidden" : ""}`}>
            <div ref={wave} />
            <div ref={spec} className="mt-1 overflow-hidden rounded-md" />
            {duration > 0 && (
              <div
                className="pointer-events-none absolute inset-y-0 rounded-sm border-x border-amber/80 bg-amber/10"
                style={{
                  left: `${(clip.window_start / duration) * 100}%`,
                  width: `${((Math.min(clip.window_end, duration) - clip.window_start) / duration) * 100}%`,
                }}
              />
            )}
          </div>
          {duration > 0 && (
            <p className="mt-1.5 flex items-center gap-1.5 text-[11px] text-white/45">
              <span className="inline-block h-2 w-3 rounded-sm border-x border-amber/80 bg-amber/20" />
              BirdNET detection · {clip.window_start.toFixed(0)}–{clip.window_end.toFixed(0)} s of {duration.toFixed(0)} s
            </p>
          )}
        </div>
      )}
    </div>
  );
}
