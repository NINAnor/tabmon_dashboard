"use client";

import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { displayName } from "@/lib/format";

// A real dawn chorus from one of our recorders (validated species above their
// calibrated thresholds), rendered once as a spectrogram image.
const DAWN = {
  image: "/header/dawn-chorus-loenderveen.webp",
  audio: "/header/dawn-chorus-loenderveen.mp3",
  seconds: 45,
  place: "Loenderveen (NL)",
  when: "26 May 2026, 06:19",
  species: [
    { species: "Locustella luscinioides", common_en: "Savi's Warbler" },
    { species: "Acrocephalus schoenobaenus", common_en: "Sedge Warbler" },
    { species: "Phylloscopus trochilus", common_en: "Willow Warbler" },
    { species: "Cuculus canorus", common_en: "Common Cuckoo" },
  ],
};

/** Spectrogram of a real dawn chorus behind a hero, with a "listen" button. */
export function DawnChorusBackdrop() {
  const strip = useRef<HTMLImageElement>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [played, setPlayed] = useState(false);

  // While playing, move the spectrogram so the sound being heard sits under the
  // playhead. The loop only runs during playback.
  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    const tick = () => {
      const img = strip.current;
      const a = audio.current;
      if (img && a) {
        const box = img.parentElement!.clientWidth;
        const x = box * 0.5 - (a.currentTime / (a.duration || DAWN.seconds)) * img.clientWidth;
        img.style.transform = `translateX(${x}px)`;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  useEffect(() => () => audio.current?.pause(), []);

  const toggle = () => {
    if (!audio.current) {
      audio.current = new Audio(DAWN.audio);
      audio.current.addEventListener("ended", () => setPlaying(false));
    }
    if (playing) {
      audio.current.pause();
      setPlaying(false);
    } else {
      void audio.current.play();
      setPlaying(true);
      setPlayed(true);
    }
  };

  return (
    <>
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-[12%] top-[18%] opacity-60 [mask-image:linear-gradient(to_bottom,transparent,black_20%,black_80%,transparent)]"
      >
        <div className="absolute inset-0 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_12%,black_88%,transparent)]">
          <img
            ref={strip}
            src={DAWN.image}
            alt=""
            className={`absolute inset-y-0 h-full w-auto max-w-none ${played ? "" : "dawn-drift"}`}
          />
          {playing && <div className="absolute inset-y-0 left-1/2 w-px bg-amber/80 shadow-[0_0_12px_#f4b860]" />}
        </div>
      </div>
      <div className="absolute right-6 top-5 z-10 flex max-w-md items-center gap-3 text-right">
        <p className="hidden text-[11px] leading-snug text-white/50 md:block">
          <span className="block whitespace-nowrap">
            {playing ? "Listening · " : "Dawn chorus · "}
            {DAWN.place}, {DAWN.when}
          </span>
          <span className="block text-white/35">{DAWN.species.map((s) => displayName(s)).join(" · ")}</span>
        </p>
        <button
          type="button"
          onClick={toggle}
          aria-label={playing ? "Pause the dawn chorus" : `Listen to the dawn chorus at ${DAWN.place}`}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-amber/50 bg-ocean-900/70 text-amber backdrop-blur hover:bg-amber/15"
        >
          {playing ? <Pause className="h-4 w-4" /> : <Play className="ml-0.5 h-4 w-4" />}
        </button>
      </div>
    </>
  );
}
