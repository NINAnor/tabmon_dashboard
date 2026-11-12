"use client";

import { Languages } from "lucide-react";
import { createContext, Fragment, useContext, useEffect, useState } from "react";
import useSWR from "swr";
import { fetcher } from "@/lib/api";
import { languageLabel, setSpeciesNames, type SpeciesNames } from "@/lib/names";

const STORAGE_KEY = "tabmon-language";

type LanguageState = { lang: string; languages: string[]; setLang: (lang: string) => void };

const LanguageContext = createContext<LanguageState>({ lang: "en", languages: ["en"], setLang: () => {} });

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const { data } = useSWR<{ languages: string[]; names: SpeciesNames }>("/api/public/species-names", fetcher, {
    revalidateOnFocus: false,
  });
  const [wanted, setWanted] = useState("en");

  useEffect(() => {
    setWanted(localStorage.getItem(STORAGE_KEY) ?? navigator.language.slice(0, 2).toLowerCase());
  }, []);

  const languages = data?.languages ?? ["en"];
  const lang = languages.includes(wanted) ? wanted : "en";
  setSpeciesNames(data?.names ?? {}, lang);

  const setLang = (next: string) => {
    localStorage.setItem(STORAGE_KEY, next);
    setWanted(next);
  };

  return (
    <LanguageContext.Provider value={{ lang, languages, setLang }}>
      {/* Remount on a language change so every species name is drawn again. */}
      <Fragment key={lang}>{children}</Fragment>
    </LanguageContext.Provider>
  );
}

export function LanguagePicker() {
  const { lang, languages, setLang } = useContext(LanguageContext);
  if (languages.length < 2) return null;
  return (
    <label className="pill relative cursor-pointer" title="Language of species names">
      <Languages className="h-3.5 w-3.5" />
      <span className="uppercase">{lang}</span>
      <select
        aria-label="Language of species names"
        value={lang}
        onChange={(e) => setLang(e.target.value)}
        className="absolute inset-0 cursor-pointer opacity-0"
      >
        {languages.map((code) => (
          <option key={code} value={code}>
            {languageLabel(code)}
          </option>
        ))}
      </select>
    </label>
  );
}
