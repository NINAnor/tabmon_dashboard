"use client";

import {
  ArrowUpRight,
  Building2,
  CalendarClock,
  Clock,
  Cpu,
  Database,
  Github,
  Headphones,
  Landmark,
  Mail,
  Moon,
  Network as NetworkIcon,
  Radio,
  Scale,
} from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { useNetwork } from "@/components/NetworkOverview";
import { fetcher, type Overview } from "@/lib/api";
import { compact, displayName, int } from "@/lib/format";
import { labLink } from "@/lib/lab";

const SECTIONS = [
  ["mission", "Mission"],
  ["methods", "Methods"],
  ["participate", "Take part"],
  ["partners", "Partners"],
  ["publications", "Publications"],
  ["resources", "Resources"],
] as const;

const WHY = [
  [Moon, "Day and night", "Recorders listen 24/7, catching nocturnal and secretive species that surveys miss."],
  [Clock, "High frequency", "Continuous time series reveal phenology, trends and early-warning signals."],
  [Scale, "Scales cheaply", "Autonomous sensors reach remote landscapes with little field effort."],
  [NetworkIcon, "Comparable", "One protocol across countries, so regions can be compared directly."],
] as const;

const WORK_PACKAGES = [
  {
    icon: Radio,
    code: "WP1",
    title: "Network deployment & data logistics",
    text: "Sites are chosen along biogeographic and land-use gradients. Solar-powered Bugg recorders stream audio over mobile networks; quality checks run from capture, and data are archived on Norway's national research infrastructure (NIRD). WP1 also contributes to a shared metadata standard for acoustic data.",
    image: "/project/device_setup.jpg",
  },
  {
    icon: Cpu,
    code: "WP2",
    title: "From AI to Essential Biodiversity Variables",
    text: "Detection models (BirdNET) and active learning turn audio into species detections with explicit uncertainty. Validations by experts and citizens calibrate the models, and detections are aggregated into indicators of occurrence, activity and phenology.",
    image: "/project/classification_pipeline_setup.jpg",
  },
  {
    icon: Database,
    code: "WP3",
    title: "Data integration & EBV showcase",
    text: "Acoustic detections differ from traditional surveys: many repeated observations with model uncertainty instead of few, curated counts. WP3 develops standards and models to combine both into harmonised Essential Biodiversity Variable products for national and European data portals.",
    image: null,
  },
];

const PARTNERS = [
  ["Norwegian Institute for Nature Research (NINA)", "Norway", "Coordinator", "https://www.nina.no/"],
  ["Naturalis Biodiversity Center", "Netherlands", null, "https://www.naturalis.nl/"],
  ["University of Amsterdam – IBED", "Netherlands", null, "https://ibed.uva.nl/"],
  ["Tilburg University – Cognitive Science & AI", "Netherlands", null, "https://www.tilburguniversity.edu/"],
  ["Statistics Netherlands (CBS)", "Netherlands", null, "https://www.cbs.nl/"],
  ["Sovon Vogelonderzoek Nederland", "Netherlands", null, "https://www.sovon.nl/"],
  ["Université de Toulon – LIS", "France", null, "https://www.lis-lab.fr/"],
  ["Forest Science and Technology Centre of Catalonia (CTFC)", "Spain", null, "https://www.ctfc.cat/"],
] as const;

const PUBLICATIONS = [
  {
    year: 2026,
    kind: "Journal article",
    title: "TABMON: Design and deployment of a transnational passive acoustic monitoring network for European birds",
    authors: "Cretois, B., Rosten, C. M., Wiel, J., Barile, C., McEwen, B., Bernard, C., … & Sethi, S.",
    venue: "Methods in Ecology and Evolution, 17(6), 1867–1879",
    url: "https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210x.70308",
  },
  {
    year: 2026,
    kind: "Journal article",
    title: "Data-driven sampling strategies for fine-tuning bird detection models",
    authors: "Bernard, C., McEwen, B., Cretois, B., Glotin, H., Stowell, D., & Marxer, R.",
    venue: "The Journal of the Acoustical Society of America, 159(6), 4891–4903",
    url: "https://pubs.aip.org/asa/jasa/article/159/6/4891/3393438",
  },
  {
    year: 2026,
    kind: "Report",
    title: "Safe and Sound Project Report: Is Camtrap DP a suitable standard for (bio)acoustic data?",
    authors: "Wiel, J. A. M.-A., Govaert, S., Cretois, B., & Desmet, P.",
    venue: "NINA Report 2731",
    url: "https://hdl.handle.net/11250/5343743",
  },
  {
    year: 2025,
    kind: "Preprint",
    title: "Stratified Active Learning for Spatiotemporal Generalisation in Large-Scale Bioacoustic Monitoring",
    authors: "McEwen, B., Bernard, C., & Stowell, D.",
    venue: "bioRxiv, 2025.09.01.673472",
    url: "https://doi.org/10.1101/2025.09.01.673472",
  },
];

const RESOURCES = [
  [Github, "TABMON", "Documentation hub linking repositories, protocols and metadata standards.", "https://github.com/NINAnor/TABMON"],
  [Cpu, "Classification pipeline", "From raw field audio to detections, uncertainty and EBVs.", "https://github.com/BenMcEwen1/TABMON-Classification-Pipeline"],
  [CalendarClock, "Yearly reports", "Automated site-level monitoring reports and visualisations.", "https://github.com/NINAnor/tabmon_reporting"],
  [Database, "Zenodo archive", "Published reports, datasets and supplementary material with DOIs.", "https://zenodo.org/records/17899019"],
] as const;

type Wanted = {
  species: string;
  common_en: string | null;
  n_detections: number;
  n_validated: number;
  needed: number;
  country: string;
  cluster: string;
};

function Section({ id, eyebrow, title, children }: { id: string; eyebrow: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-32 border-t border-white/5 py-14">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="mt-2 max-w-3xl font-serif text-3xl md:text-4xl">{title}</h2>
      <div className="mt-6">{children}</div>
    </section>
  );
}

export function ProjectPage() {
  const { data: overview } = useSWR<Overview>("/api/public/overview", fetcher);
  const { data: network } = useNetwork();
  const { data: wanted } = useSWR<Wanted[]>("/api/public/most-wanted?limit=8", fetcher);
  const p = network?.pipeline;
  const tb = p?.size_tb ?? null;

  return (
    <div className="mx-auto max-w-7xl px-6">
      {/* Intro */}
      <div className="grid items-center gap-10 pb-10 pt-12 lg:grid-cols-[1fr_1fr]">
        <div>
          <p className="eyebrow">Biodiversa+ · Horizon Europe · 2024–2027</p>
          <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">
            Towards a Transnational Acoustic Biodiversity Monitoring Network
          </h1>
          <p className="mt-4 text-white/65">
            TABMON builds a standardised passive acoustic monitoring network across Europe, from the Arctic to the
            Mediterranean, and turns soundscapes into policy-relevant biodiversity indicators that complement
            traditional surveys and support the EU Biodiversity Strategy 2030.
          </p>
          <p className="mt-4 text-sm text-white/50">
            Coordinated by the Norwegian Institute for Nature Research (NINA) · Project leader{" "}
            <span className="text-white/80">Benjamin Cretois</span>
          </p>
        </div>
        <img
          src="/project/figure_grant.png"
          alt="TABMON overview: from field recorders to biodiversity indicators"
          className="w-full rounded-2xl border border-white/10 bg-white"
        />
      </div>

      {/* At a glance (live) */}
      <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-4">
        {[
          ["Recorders", overview ? int(overview.devices) : "–", "deployed in the field"],
          ["Audio archived", tb ? `${tb.toFixed(0)} TB` : "–", `${compact(p?.files ?? null)} five-minute files`],
          ["Countries", overview ? overview.countries : "–", "Norway · Netherlands · France · Spain"],
          ["Species detected", overview ? int(overview.n_species) : "–", "identified by BirdNET"],
        ].map(([k, v, sub]) => (
          <div key={k as string} className="bg-ocean-900 px-5 py-4">
            <dt className="eyebrow">{k}</dt>
            <dd className="mt-1 font-serif text-3xl tabular-nums">{v}</dd>
            <dd className="text-xs text-white/45">{sub}</dd>
          </div>
        ))}
      </dl>

      {/* In-page navigation */}
      <nav className="sticky top-16 z-30 -mx-6 mt-8 flex gap-1 overflow-x-auto border-b border-white/5 bg-ocean-900/90 px-6 py-2 backdrop-blur">
        {SECTIONS.map(([id, label]) => (
          <a key={id} href={`#${id}`} className="whitespace-nowrap rounded-full px-3 py-1 text-sm text-white/60 hover:bg-white/5 hover:text-white">
            {label}
          </a>
        ))}
      </nav>

      <Section id="mission" eyebrow="Mission" title="Why listen to biodiversity?">
        <p className="max-w-3xl text-white/65">
          We operationalise a pan-European network of autonomous acoustic sensors and AI pipelines that convert
          soundscapes into Essential Biodiversity Variables (EBVs). The aim is to fill gaps in reporting for EU
          directives with high-frequency, comparable data from four biogeographic regions.
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-4">
          {WHY.map(([Icon, title, text]) => (
            <div key={title} className="card p-5">
              <Icon className="h-5 w-5 text-teal" />
              <p className="mt-3 font-serif text-lg">{title}</p>
              <p className="mt-1 text-sm text-white/55">{text}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="methods" eyebrow="Methods" title="Three work packages, from sensor to indicator">
        <div className="space-y-5">
          {WORK_PACKAGES.map((wp) => (
            <div key={wp.code} className={`card grid gap-6 p-5 ${wp.image ? "md:grid-cols-[1fr_360px]" : ""}`}>
              <div>
                <div className="flex items-center gap-2">
                  <wp.icon className="h-5 w-5 text-teal" />
                  <span className="rounded-full bg-teal/15 px-2 py-0.5 text-xs text-teal">{wp.code}</span>
                </div>
                <p className="mt-3 font-serif text-2xl">{wp.title}</p>
                <p className="mt-2 text-white/60">{wp.text}</p>
              </div>
              {wp.image && <img src={wp.image} alt={wp.title} className="w-full rounded-xl object-cover" loading="lazy" />}
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-white/50">
          See the pipeline in numbers on the{" "}
          <Link href="/" className="text-teal hover:underline">
            Network
          </Link>{" "}
          tab, and how calibrated detections become phenology on the{" "}
          <Link href="/species" className="text-teal hover:underline">
            Species
          </Link>{" "}
          tab.
        </p>
      </Section>

      <Section id="participate" eyebrow="Take part" title="Lend us your ears">
        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <div className="card border-amber/30 bg-amber/[0.04] p-6">
            <Headphones className="h-6 w-6 text-amber" />
            <p className="mt-3 font-serif text-2xl">The Listening Lab</p>
            <p className="mt-2 text-white/65">
              BirdNET is good but not perfect. In the Listening Lab you hear short clips from our recorders and
              tell us whether the bird it suggests is really there. Every yes or no sets the confidence threshold
              that all charts on this site use, so your ears directly make the results more reliable.
            </p>
            {p && (
              <p className="mt-4 text-sm text-white/70">
                So far <b className="text-amber">{int(p.citizen_validated)}</b> citizen and{" "}
                <b className="text-amber">{int(p.expert_validated)}</b> expert checks have calibrated{" "}
                <b className="text-amber">{p.calibrated}</b> species.
              </p>
            )}
            <a
              href={labLink()}
              target="_blank"
              rel="noreferrer"
              className="mt-5 inline-flex items-center gap-2 rounded-full bg-amber px-5 py-2.5 text-sm font-medium text-ocean-950 hover:bg-amber/90"
            >
              Start listening <ArrowUpRight className="h-4 w-4" />
            </a>
          </div>
          <div className="card p-6">
            <p className="eyebrow">Most wanted · often detected, rarely checked</p>
            <ul className="mt-3 divide-y divide-white/5">
              {wanted?.map((w) => (
                <li key={w.species} className="flex items-center gap-3 py-2.5">
                  <div className="min-w-0 flex-1">
                    <Link href={`/species?species=${encodeURIComponent(w.species)}`} className="truncate hover:text-teal">
                      {displayName(w)}
                    </Link>
                    <p className="text-xs text-white/45">
                      {compact(w.n_detections)} detections · {w.n_validated} checked · {w.needed} more needed
                    </p>
                  </div>
                  <a
                    href={labLink({ country: w.country, cluster: w.cluster, species: w.species })}
                    target="_blank"
                    rel="noreferrer"
                    className="shrink-0 rounded-full bg-amber/15 px-3 py-1 text-xs text-amber hover:bg-amber/25"
                  >
                    Validate →
                  </a>
                </li>
              ))}
              {!wanted && <li className="h-60 animate-pulse rounded bg-white/5" />}
            </ul>
          </div>
        </div>
      </Section>

      <Section id="partners" eyebrow="Partners" title="A European consortium">
        <p className="mb-5 max-w-3xl text-white/60">
          Coordinated by NINA and led by <span className="text-white">Benjamin Cretois</span>, with research
          institutes, universities, statistics offices and bird-monitoring organisations in four countries. Funded by{" "}
          <a href="https://www.biodiversa.eu/" target="_blank" rel="noreferrer" className="text-teal hover:underline">
            Biodiversa+
          </a>{" "}
          with national funding agencies.
        </p>
        <ul className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {PARTNERS.map(([name, country, role, url]) => (
            <li key={name}>
              <a href={url} target="_blank" rel="noreferrer" className="card flex h-full items-start gap-3 p-4 hover:bg-white/[0.06]">
                {role ? <Landmark className="mt-0.5 h-4 w-4 shrink-0 text-amber" /> : <Building2 className="mt-0.5 h-4 w-4 shrink-0 text-teal" />}
                <span>
                  <span className="block text-sm">{name}</span>
                  <span className="text-xs text-white/45">
                    {country}
                    {role ? ` · ${role}` : ""}
                  </span>
                </span>
              </a>
            </li>
          ))}
        </ul>
      </Section>

      <Section id="publications" eyebrow="Publications" title="Research output">
        <ol className="space-y-3">
          {PUBLICATIONS.map((pub) => (
            <li key={pub.title}>
              <a href={pub.url} target="_blank" rel="noreferrer" className="card group flex gap-5 p-5 hover:bg-white/[0.06]">
                <span className="font-serif text-2xl text-white/35">{pub.year}</span>
                <span className="min-w-0 flex-1">
                  <span className="rounded-full bg-white/5 px-2 py-0.5 text-[11px] text-white/60">{pub.kind}</span>
                  <span className="mt-1.5 block font-medium group-hover:text-teal">{pub.title}</span>
                  <span className="block text-sm text-white/50">{pub.authors}</span>
                  <span className="block text-sm italic text-white/40">{pub.venue}</span>
                </span>
                <ArrowUpRight className="h-4 w-4 shrink-0 text-white/30 group-hover:text-teal" />
              </a>
            </li>
          ))}
        </ol>
      </Section>

      <Section id="resources" eyebrow="Resources" title="Code, data and contact">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {RESOURCES.map(([Icon, title, text, url]) => (
            <a key={title} href={url} target="_blank" rel="noreferrer" className="card p-5 hover:bg-white/[0.06]">
              <Icon className="h-5 w-5 text-teal" />
              <p className="mt-3 font-medium">{title}</p>
              <p className="mt-1 text-sm text-white/55">{text}</p>
            </a>
          ))}
        </div>
        <a href="mailto:benjamin.cretois@nina.no" className="mt-6 inline-flex items-center gap-2 text-sm text-teal hover:underline">
          <Mail className="h-4 w-4" /> Contact the project: benjamin.cretois@nina.no
        </a>
      </Section>
    </div>
  );
}
